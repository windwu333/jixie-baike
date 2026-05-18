#!/usr/bin/env python3
"""机械师大百科 — arXiv mechanical engineering paper scraper.

Target categories: fluid dynamics, materials science, classical physics,
robotics, systems & control, numerical analysis/FEM, electrical systems.
Plus keyword searches for broader mechanical engineering coverage.

Output: JSON records with arxiv_id, title, abstract, authors, categories,
published date, and URL. Target 1000-2000 records.
"""

import logging
import re
import sys
import time
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

# Allow import of framework.py from sibling directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from framework import cached_get, log, save_raw

log = logging.getLogger("arxiv")

ARXIV_API = "https://export.arxiv.org/api/query"

# Namespace map for arXiv Atom XML
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}

# Mechanical-engineering-relevant arXiv categories
CATEGORIES = [
    "physics.flu-dyn",      # Fluid Dynamics
    "cond-mat.mtrl-sci",    # Materials Science
    "physics.class-ph",     # Classical Physics
    "cs.RO",                # Robotics
    "cs.SY",                # Systems & Control
    "math.NA",              # Numerical Analysis / FEM
    "eess.SY",              # Electrical Systems & Control
]

# Broader keyword searches to catch cross-domain papers
KEYWORD_QUERIES = [
    'all:"mechanical engineering"',
    'all:"finite element"',
    'all:"solid mechanics"',
    'all:"structural dynamics"',
    'all:"manufacturing"',
    # Extra keywords from second pass
    'all:"machine design"',
    'all:"stress analysis"',
    'all:"CAD"',
    'all:"metallurgy"',
    'all:"corrosion"',
    'all:"tribology"',
    'all:"composite materials"',
]

# Extra categories from second pass
EXTRA_CATEGORIES = [
    "physics.app-ph",        # Applied Physics
    "cond-mat.mes-hall",     # Mesoscale & Nanoscale Physics
    "physics.chem-ph",       # Chemical Physics
    "physics.ins-det",       # Instrumentation & Detectors
    "physics.optics",        # Optics
    "cond-mat.soft",         # Soft Condensed Matter
]

MAX_PER_PAGE = 100
MAX_TOTAL = 1000
# arXiv Terms of Service: no more than 1 request per 3 seconds
RATE_LIMIT_SEC = 3.0


class ArxivMechScraper:
    """Scrape mechanical-engineering-related papers from arXiv."""

    def __init__(self):
        self._last_req = 0.0

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_req
        if elapsed < RATE_LIMIT_SEC:
            time.sleep(RATE_LIMIT_SEC - elapsed)
        self._last_req = time.time()

    # ------------------------------------------------------------------
    # HTTP / XML
    # ------------------------------------------------------------------

    def _fetch_page(self, query: str, start: int) -> str | None:
        """Fetch one page (max 100 results) from the arXiv API."""
        self._throttle()
        params = {
            "search_query": query,
            "start": str(start),
            "max_results": str(MAX_PER_PAGE),
        }
        try:
            return cached_get(ARXIV_API, params=params)
        except Exception as exc:
            log.error("Fetch error (query=%s, start=%d): %s", query[:60], start, exc)
            return None

    @staticmethod
    def _parse_entry(entry: Any) -> dict[str, Any] | None:
        """Parse a single Atom <entry> into a structured record.

        arXiv * 2015+ uses the canonical ID format
        ``http://arxiv.org/abs/XXXX.XXXXX``.  Older papers use a different
        pattern (``arXiv:astro-ph/XXXX``) — the regex handles both.
        """
        def _text(tag: str) -> str:
            el = entry.find(tag, NS)
            return el.text.strip() if el is not None and el.text else ""

        # --- arXiv ID ---------------------------------------------------
        raw_id = _text("atom:id")
        if not raw_id:
            return None
        m = re.search(r"(?:abs/|arXiv:)(\S+)", raw_id)
        if not m:
            return None
        # Strip version suffix (e.g. v1, v2) to get canonical arXiv ID
        arxiv_id = re.sub(r"v\d+$", "", m.group(1))

        # --- Title & abstract -------------------------------------------
        title = _text("atom:title")
        abstract = _text("atom:summary")
        published = _text("atom:published")[:10]  # keep YYYY-MM-DD

        # --- Authors ----------------------------------------------------
        authors: list[str] = []
        for author_el in entry.findall("atom:author", NS):
            name_el = author_el.find("atom:name", NS)
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())

        # --- Categories -------------------------------------------------
        categories: list[str] = []
        primary = entry.find("arxiv:primary_category", NS)
        if primary is not None:
            term = primary.get("term", "")
            if term:
                categories.append(term)
        for cat_el in entry.findall("atom:category", NS):
            term = cat_el.get("term", "")
            if term and term not in categories:
                categories.append(term)

        return {
            "arxiv_id": arxiv_id,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "categories": categories,
            "published": published,
            "url": raw_id,
        }

    @staticmethod
    def _parse_page(xml_text: str) -> list[dict[str, Any]]:
        """Parse Atom XML response into a list of record dicts."""
        root = ElementTree.fromstring(xml_text)
        records: list[dict[str, Any]] = []
        for entry in root.findall("atom:entry", NS):
            record = ArxivMechScraper._parse_entry(entry)
            if record and record["title"]:
                records.append(record)
        return records

    # ------------------------------------------------------------------
    # Query pagination
    # ------------------------------------------------------------------

    def _scrape_query(self, query: str, label: str) -> list[dict[str, Any]]:
        """Paginate through a query, stopping at 0 results or MAX_TOTAL."""
        records: list[dict[str, Any]] = []
        seen: set[str] = set()

        for start in range(0, MAX_TOTAL, MAX_PER_PAGE):
            xml_text = self._fetch_page(query, start)
            if xml_text is None:
                log.warning("  [%s] aborting at start=%d due to fetch error", label, start)
                break

            page = self._parse_page(xml_text)
            if not page:
                log.info("  [%s] no more records at start=%d", label, start)
                break

            new = [r for r in page if r["arxiv_id"] not in seen]
            for r in new:
                seen.add(r["arxiv_id"])
            records.extend(new)

            log.info("  [%s] start=%d got=%d new=%d total=%d",
                     label, start, len(page), len(new), len(records))

            if len(page) < MAX_PER_PAGE:
                break  # exhausted

        return records

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def scrape_category(self, category: str) -> list[dict[str, Any]]:
        """Scrape papers in a single arXiv category."""
        query = f"cat:{category}"
        log.info("Category: %s", category)
        return self._scrape_query(query, category)

    def scrape_keyword(self, keyword: str) -> list[dict[str, Any]]:
        """Scrape papers matching a keyword search."""
        log.info("Keyword: %s", keyword)
        return self._scrape_query(keyword, "keyword")

    def run(self) -> list[dict[str, Any]]:
        """Scrape all configured categories and keyword queries.

        Deduplicates across runs so a paper appearing in multiple categories
        is only stored once.
        """
        all_records: list[dict[str, Any]] = []
        seen: set[str] = set()

        for cat in CATEGORIES + EXTRA_CATEGORIES:
            records = self.scrape_category(cat)
            new = [r for r in records if r["arxiv_id"] not in seen]
            for r in new:
                seen.add(r["arxiv_id"])
            all_records.extend(new)
            log.info("  => %s: %d new (total %d)", cat, len(new), len(all_records))

        for kw in KEYWORD_QUERIES:
            records = self.scrape_keyword(kw)
            new = [r for r in records if r["arxiv_id"] not in seen]
            for r in new:
                seen.add(r["arxiv_id"])
            all_records.extend(new)
            log.info("  => keyword: %d new (total %d)", len(new), len(all_records))

        return all_records


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    scraper = ArxivMechScraper()
    results = scraper.run()
    out = save_raw("arxiv-me", results)
    log.info("Done. %d papers saved → %s", len(results), out)
