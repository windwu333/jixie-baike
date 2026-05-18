#!/usr/bin/env python3
"""机械师大百科 — NASA NTRS (Technical Reports Server) 采集引擎

API:  GET /api/citations/search?q=<query>&size=10
       (deprecated by NASA but active; max 10 results per query, no pagination)

Strategy:
  - The search API caps at 10 results and ignores ?from= (pagination broken).
  - To get diverse records we fire many narrow queries: each keyword x year.
  - Deduplicate globally by submission ID (numeric id field).
  - Respect 0.5 s rate limit between API calls.

Reference:
  OpenAPI spec: https://ntrs.nasa.gov/api/openapi/
  Harvesting:   https://sti.nasa.gov/harvesting-data-from-ntrs/

Usage:
  python3 scrapers/engines/nasa_ntrs_scraper.py
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

import requests

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
from framework import cached_get, sanitize, save_raw, session  # noqa: E402

log = logging.getLogger("nasa_ntrs")

SOURCE_ID = "nasa-ntrs"
BASE_URL = "https://ntrs.nasa.gov"
SEARCH_URL = f"{BASE_URL}/api/citations/search"

# Broad keywords from task spec
BROAD_KEYWORDS = [
    "mechanical engineering",
    "materials science",
    "structural analysis",
    "heat transfer",
    "fluid dynamics",
    "aerospace structures",
    "tribology",
    "manufacturing",
    # Extra keywords from second pass
    "machine design",
    "stress analysis",
    "CAD",
    "finite element",
    "metallurgy",
    "corrosion",
    "composite materials",
]

# Years with non-trivial NTRS holdings (from aggregations)
YEARS = list(range(1960, 2026))  # 66 years

RATE_LIMIT_SECS = 0.5
TARGET_TOTAL = 1000


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _flatten_authors(raw: list[dict]) -> str:
    """Extract author names from authorAffiliations array."""
    names: list[str] = []
    for aff in raw:
        meta = aff.get("meta") or {}
        author = meta.get("author") or {}
        name = author.get("name", "")
        if name:
            names.append(name)
    return "; ".join(names)


def _pick_date(submission: dict) -> str:
    """Best available date string (distributionDate > submittedDate > created)."""
    for key in ("distributionDate", "submittedDate", "created"):
        val = submission.get(key)
        if val:
            return str(val)[:10]
    return ""


def _normalise(raw: dict) -> dict[str, Any]:
    """Map verbose API response to our compact schema."""
    sid = raw.get("id") or raw.get("submissionId", 0)
    subjects = raw.get("subjectCategories") or []
    authors = _flatten_authors(raw.get("authorAffiliations") or [])
    return {
        "id": str(sid),
        "title": sanitize(raw.get("title", "")),
        "abstract": sanitize(raw.get("abstract", "")),
        "authors": authors,
        "date": _pick_date(raw),
        "subjects": subjects,
        "url": f"{BASE_URL}/citations/{sid}",
        "sti_type": raw.get("stiType", ""),
        "keywords": raw.get("keywords") or [],
        "center": (raw.get("center") or {}).get("code", ""),
    }


def _execute_query(query: str, sess: requests.Session) -> list[dict[str, Any]]:
    """Execute one query, return normalised records (max ~10)."""
    raw_text = cached_get(SEARCH_URL, params={"q": query, "size": 10}, ttl=86400, sess=sess)
    body = json.loads(raw_text)
    return body.get("results") or []


# ---------------------------------------------------------------------------
# scraper class
# ---------------------------------------------------------------------------

class NasaNtrsScraper:
    """Scrape NTRS metadata via /api/citations/search using multi-dimensional query expansion."""

    def __init__(self):
        self.seen: set[str] = set()
        self.sess: requests.Session | None = None
        self._last_call = 0.0

    def _rlimit(self):
        elapsed = time.time() - self._last_call
        if elapsed < RATE_LIMIT_SECS:
            time.sleep(RATE_LIMIT_SECS - elapsed)
        self._last_call = time.time()

    def _query(self, q: str) -> list[dict[str, Any]]:
        """Query once, return new (unseen) normalised records."""
        if self.sess is None:
            self.sess = session(retries=3, backoff=1.0, timeout=30)
        self._rlimit()
        items = _execute_query(q, self.sess)
        batch: list[dict[str, Any]] = []
        for item in items:
            sid = str(item.get("id") or item.get("submissionId", 0))
            if sid in self.seen:
                continue
            self.seen.add(sid)
            batch.append(_normalise(item))
        return batch

    def scrape_all(self) -> list[dict[str, Any]]:
        """Run broad + year-specific queries, deduplicate globally, return records."""
        all_results: list[dict[str, Any]] = []

        # Phase 1: broad keywords (no year filter)
        for kw in BROAD_KEYWORDS:
            batch = self._query(kw)
            all_results.extend(batch)
            log.info("  broad %-30s → %2d new  (total seen: %d)", kw, len(batch), len(self.seen))
            if len(self.seen) >= TARGET_TOTAL:
                break

        if len(self.seen) >= TARGET_TOTAL:
            return all_results

        # Phase 2: year-specific queries for each keyword
        # Each "keyword YEAR" returns a different top-N slice
        for kw in BROAD_KEYWORDS:
            if len(self.seen) >= TARGET_TOTAL:
                break
            for year in YEARS:
                if len(self.seen) >= TARGET_TOTAL:
                    break
                q = f"{kw} {year}"
                batch = self._query(q)
                if batch:
                    all_results.extend(batch)
                    log.info("  %-40s → %2d new  (total seen: %d)", q, len(batch), len(self.seen))

        log.info(
            "Total: %d unique records (seen set: %d)",
            len(all_results), len(self.seen),
        )
        return all_results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    scraper = NasaNtrsScraper()
    records = scraper.scrape_all()
    path = save_raw(SOURCE_ID, records)
    print(f"\nSaved {len(records)} records → {path}")
