#!/usr/bin/env python3
"""机械师大百科 — 原始语料去重+质量评分+索引管线 (A15+A16)"""

import json, logging, re, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "raw"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("ingest")

# Source quality tiers
SOURCE_QUALITY = {
    "nist-engineering":        {"tier": "A", "weight": 1.0, "desc": "US Gov standard reference"},
    "nasa-ntrs":               {"tier": "A", "weight": 1.0, "desc": "NASA technical reports"},
    "engineers-edge":          {"tier": "B", "weight": 0.8, "desc": "Engineering portal"},
    "engineering-toolbox":     {"tier": "B", "weight": 0.8, "desc": "Engineering data portal"},
    "efunda":                  {"tier": "B", "weight": 0.8, "desc": "Engineering portal"},
    "britannica-engineering":  {"tier": "B", "weight": 0.8, "desc": "General encyclopedia"},
    "arxiv-me":                {"tier": "B", "weight": 0.7, "desc": "Preprint abstracts"},
    "explainthatstuff":        {"tier": "C", "weight": 0.6, "desc": "Popular science"},
    "howstuffworks-eng":       {"tier": "C", "weight": 0.6, "desc": "Popular science"},
    "intechopen-engineering":  {"tier": "C", "weight": 0.6, "desc": "OA publisher (mixed quality)"},
}


def collect_all_raw() -> list[dict]:
    """Load all JSON files from raw/<source_id>/ directories."""
    records = []
    for src_dir in sorted(RAW.iterdir()):
        if not src_dir.is_dir() or src_dir.name == ".cache":
            continue
        source_id = src_dir.name
        for f in sorted(src_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text())
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            item["_source_id"] = source_id
                            item["_source_file"] = str(f)
                            records.append(item)
                elif isinstance(data, dict):
                    # Handle dict-wrapped lists
                    for key in data:
                        val = data[key]
                        if isinstance(val, list):
                            for item in val:
                                if isinstance(item, dict):
                                    item["_source_id"] = source_id
                                    item["_source_file"] = str(f)
                                    records.append(item)
            except Exception as e:
                log.warning("Failed to parse %s: %s", f, e)
    return records


def dedup(records: list[dict]) -> list[dict]:
    """Deduplicate by URL or title similarity."""
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    deduped = []
    dup_count = 0
    for r in records:
        url = r.get("url", "") or r.get("source_url", "")
        title = (r.get("title", "") or "").strip().lower()
        # URL dedup
        if url and url in seen_urls:
            dup_count += 1
            continue
        # Title dedup (for records without URLs)
        if not url and title:
            if title in seen_titles:
                dup_count += 1
                continue
            seen_titles.add(title)
        if url:
            seen_urls.add(url)
        deduped.append(r)
    if dup_count:
        log.info("  Dedup removed %d duplicate records", dup_count)
    return deduped


def score_record(rec: dict) -> dict:
    """Score a record for quality."""
    source_id = rec.get("_source_id", "unknown")
    sq = SOURCE_QUALITY.get(source_id, {"tier": "C", "weight": 0.5, "desc": "Unknown"})

    # Content length score
    content = rec.get("content", "") or rec.get("abstract", "") or ""
    content_len = len(content)
    if content_len > 3000:
        len_score = 1.0
    elif content_len > 1000:
        len_score = 0.8
    elif content_len > 250:
        len_score = 0.6
    elif content_len > 80:
        len_score = 0.45
    elif content_len > 30:
        len_score = 0.3
    else:
        len_score = 0.1

    # Title quality
    title = rec.get("title", "") or ""
    has_title = 0.15 if len(title) > 5 else 0.0

    # Source quality
    source_score = sq["weight"]

    overall = (len_score * 0.45) + (has_title * 0.15) + (source_score * 0.40)

    return {
        "quality_score": round(overall, 2),
        "content_length": content_len,
        "has_title": len(title) > 5,
        "source_tier": sq["tier"],
        "source_desc": sq["desc"],
    }


def build_index(records: list[dict]) -> dict:
    """Build a summary index of all collected data."""
    sources = Counter()
    tiers = Counter()
    total_content_len = 0
    scores = []

    for r in records:
        sid = r.get("_source_id", "unknown")
        sources[sid] += 1
        sq = SOURCE_QUALITY.get(sid, {"tier": "C"})
        tiers[sq["tier"]] += 1
        content = r.get("content", "") or r.get("abstract", "") or ""
        total_content_len += len(content)

    scored = [score_record(r) for r in records]
    avg_score = sum(s["quality_score"] for s in scored) / len(scored) if scored else 0

    return {
        "total_records": len(records),
        "sources": dict(sources.most_common()),
        "tiers": dict(tiers.most_common()),
        "avg_quality_score": round(avg_score, 3),
        "total_content_chars": total_content_len,
        "total_content_kb": round(total_content_len / 1024, 1),
        "scored_below_0_5": sum(1 for s in scored if s["quality_score"] < 0.5),
        "scored_0_5_to_0_8": sum(1 for s in scored if 0.5 <= s["quality_score"] < 0.8),
        "scored_above_0_8": sum(1 for s in scored if s["quality_score"] >= 0.8),
    }


def main():
    log.info("=" * 60)
    log.info("A15: 原始语料去重 + 质量评分 + 索引管线")
    log.info("=" * 60)

    # Phase 1: collect
    log.info("Phase 1: Collecting raw data...")
    records = collect_all_raw()
    log.info("  Collected %d raw records from %d source dirs",
             len(records), len(set(r.get("_source_id", "?") for r in records)))

    # Phase 2: dedup
    log.info("Phase 2: Deduplicating...")
    deduped = dedup(records)
    log.info("  After dedup: %d records", len(deduped))

    # Phase 3: score and build index
    log.info("Phase 3: Scoring and indexing...")
    index = build_index(deduped)

    log.info("")
    log.info("=" * 60)
    log.info("INDEX SUMMARY")
    log.info("=" * 60)
    log.info("Total records:         %d", index["total_records"])
    log.info("Source distribution:   %s", json.dumps(index["sources"], ensure_ascii=False))
    log.info("Quality tiers:         %s", json.dumps(index["tiers"]))
    log.info("Avg quality score:     %.3f", index["avg_quality_score"])
    log.info("Total content:         %d chars (%s KB)",
             index["total_content_chars"], index["total_content_kb"])
    log.info("Quality distribution:  <0.5: %d | 0.5-0.8: %d | >0.8: %d",
             index["scored_below_0_5"], index["scored_0_5_to_0_8"], index["scored_above_0_8"])

    # Save index
    index_path = RAW / ".index.json"
    index["generated_at"] = datetime.now(timezone.utc).isoformat()
    index["gate_pass"] = index["total_records"] >= 5000 and index["avg_quality_score"] >= 0.6
    index["records"] = []
    # Save scored records too (omit huge content)
    scored_records = []
    for r in deduped:
        sr = score_record(r)
        scored_records.append({
            "url": r.get("url", "") or r.get("source_url", ""),
            "title": r.get("title", "")[:100],
            "source_id": r.get("_source_id", ""),
            "content_length": sr["content_length"],
            "quality_score": sr["quality_score"],
            "source_tier": sr["source_tier"],
        })
    index["records"] = scored_records
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2))
    log.info("Index saved → %s", index_path)

    # Gate check A16
    log.info("")
    log.info("=" * 60)
    log.info("A16: 门禁检查 — 原始语料库就绪 ≥ 5000条")
    log.info("=" * 60)
    passed = index["total_records"] >= 5000
    qual_ok = index["avg_quality_score"] >= 0.6
    log.info("  记录数 ≥ 5000:       %s (%d)", "✅" if passed else "❌", index["total_records"])
    log.info("  平均质量分 ≥ 0.6:   %s (%.3f)", "✅" if qual_ok else "❌", index["avg_quality_score"])
    if passed and qual_ok:
        log.info("  🎉 GATE PASSED! Phase A complete. Ready for Phase B.")
    else:
        log.info("  ⛔ GATE NOT PASSED. Need more data.")

    return index


if __name__ == "__main__":
    main()
