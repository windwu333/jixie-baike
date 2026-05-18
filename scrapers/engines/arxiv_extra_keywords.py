#!/usr/bin/env python3
"""机械师大百科 — arXiv extra keyword queries, with conservative rate limiting."""

import json
import logging
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
from framework import cached_get, save_raw, session  # noqa: E402

log = logging.getLogger("arxiv_extra")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

ARXIV_API = "https://export.arxiv.org/api/query"
RATE_LIMIT_SEC = 8.0  # very conservative to avoid 429s
MAX_PER_PAGE = 100

# Extra keywords not in original run
EXTRA_KEYWORDS = [
    'all:"machine design"',
    'all:"stress analysis"',
    'all:"CAD"',
    'all:"metallurgy"',
    'all:"corrosion"',
    'all:"tribology"',
    'all:"composite materials"',
]

# Extra categories not in original run (the ones that got 429'd)
EXTRA_CATEGORIES = [
    "physics.app-ph",
    "cond-mat.mes-hall",
    "physics.chem-ph",
    "physics.ins-det",
    "physics.optics",
    "cond-mat.soft",
]


def fetch_with_backoff(query: str, start: int) -> str | None:
    """Fetch with up to 3 attempts, doubling delay each time on failure."""
    for attempt in range(3):
        delay = RATE_LIMIT_SEC * (2 ** attempt)
        time.sleep(delay)
        try:
            sess = session(retries=1, backoff=5.0, timeout=60)
            params = {"search_query": query, "start": str(start), "max_results": str(MAX_PER_PAGE)}
            return cached_get(ARXIV_API, params=params, sess=sess)
        except Exception as exc:
            log.warning("  attempt %d/3 failed for %s start=%d: %s", attempt + 1, query[:50], start, exc)
    return None


def main():
    all_records = []
    seen: set[str] = set()
    source = "arxiv-me"

    # Load existing records to avoid re-fetching what we already have
    existing_dir = Path(__file__).parent.parent.parent / "raw" / source
    if existing_dir.exists():
        for f in sorted(existing_dir.glob("*.json")):
            existing = json.loads(f.read_text())
            for r in existing:
                aid = r.get("arxiv_id", "")
                if aid:
                    seen.add(aid)
    log.info("Loaded %d existing records from %s", len(seen), source)

    # Hard-limit to avoid excessive API usage
    MAX_PER_QUERY = 300

    for cat in EXTRA_CATEGORIES:
        query = f"cat:{cat}"
        log.info("Category: %s", cat)
        records = []
        for start in range(0, MAX_PER_QUERY, MAX_PER_PAGE):
            xml_text = fetch_with_backoff(query, start)
            if xml_text is None:
                log.warning("  %s: giving up at start=%d", cat, start)
                break
            # Minimal XML parsing
            import re
            entries = xml_text.split("<entry>")[1:]  # quick split
            if not entries:
                log.info("  %s: no more at start=%d", cat, start)
                break
            got = len(entries)
            recs = 0
            for entry in entries:
                m = re.search(r"<id>.*?(abs/|arXiv:)(\S+?)<", entry)
                if not m:
                    continue
                arxiv_id = re.sub(r"v\d+$", "", m.group(2))
                if arxiv_id in seen:
                    continue
                seen.add(arxiv_id)
                title_m = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
                title = re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else ""
                abs_m = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
                abstract = re.sub(r"\s+", " ", abs_m.group(1)).strip() if abs_m else ""
                authors = re.findall(r"<name>(.*?)</name>", entry)
                # categories
                cats = re.findall(r'term="([^"]+)"', entry)
                pub_m = re.search(r"<published>(.*?)</published>", entry)
                published = pub_m.group(1)[:10] if pub_m else ""
                records.append({
                    "arxiv_id": arxiv_id,
                    "title": title,
                    "abstract": abstract,
                    "authors": authors,
                    "categories": cats,
                    "published": published,
                    "url": f"http://arxiv.org/abs/{arxiv_id}",
                })
                recs += 1
            log.info("  %s start=%d got=%d new=%d total=%d", cat, start, got, recs, len(records))
        all_records.extend(records)
        log.info("  => %s: %d new (total this run: %d)", cat, len(records), len(all_records))

        # Incremental save after each category
        if records:
            ts = time.strftime("%Y%m%d_%H%M%S")
            path = save_raw(source, records, filename=f"{ts}_extra_{cat.replace('.', '-')}.json")
            log.info("  Saved %d records to %s", len(records), path)

    for kw in EXTRA_KEYWORDS:
        log.info("Keyword: %s", kw)
        xml_text = fetch_with_backoff(kw, 0)
        if xml_text is None:
            log.warning("  %s: giving up", kw)
            continue
        import re
        entries = xml_text.split("<entry>")[1:]
        if not entries:
            log.info("  %s: no records", kw)
            continue
        records = []
        for entry in entries:
            m = re.search(r"<id>.*?(abs/|arXiv:)(\S+?)<", entry)
            if not m:
                continue
            arxiv_id = re.sub(r"v\d+$", "", m.group(2))
            if arxiv_id in seen:
                continue
            seen.add(arxiv_id)
            title_m = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
            title = re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else ""
            abs_m = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
            abstract = re.sub(r"\s+", " ", abs_m.group(1)).strip() if abs_m else ""
            authors = re.findall(r"<name>(.*?)</name>", entry)
            cats = re.findall(r'term="([^"]+)"', entry)
            pub_m = re.search(r"<published>(.*?)</published>", entry)
            published = pub_m.group(1)[:10] if pub_m else ""
            records.append({
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "categories": cats,
                "published": published,
                "url": f"http://arxiv.org/abs/{arxiv_id}",
            })
        all_records.extend(records)
        log.info("  => %s: %d new (total this run: %d)", kw, len(records), len(all_records))
        if records:
            ts = time.strftime("%Y%m%d_%H%M%S")
            kw_short = kw.replace('"', '').replace('all:', '').replace(' ', '_')
            path = save_raw(source, records, filename=f"{ts}_extra_{kw_short}.json")
            log.info("  Saved %d records to %s", len(records), path)

    log.info("DONE. Extra pass added %d new records to %s", len(all_records), source)
    print(f"Extra pass added {len(all_records)} new arXiv records")


if __name__ == "__main__":
    main()
