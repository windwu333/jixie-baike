#!/usr/bin/env python3
"""Merge mech-terminology v2 + v3 → v4 unified terminology

v2: 5049 terms (all zh/en/category, 1901 definition) + 554 extras
v3: 645 terms (all zh/en/category/description) + 4454 extras (subset of v2)

Merge strategy:
  1. Start with ALL v2 terms (5049), fill descriptions from v3 where v2 lacks definition
  2. Map v2 categories → catalog names via CAT_MAP
  3. Combine v2_extras + v3_extras, deduplicate by English term
  4. Write merged v4
"""
import json, sys
from pathlib import Path

KB = Path(__file__).parent.parent / "knowledge-base"

# Old → new category mapping (from batch-article-defs.py)
CAT_MAP = {
    "制图CAD": "机械制图与CAD",
    "力学强度": "力学与强度分析",
    "热工流体": "热工与流体",
    "机电自动化": "机械电子与自动化",
    "标准规范": "标准与规范",
    "未分类": "未分类",
}


def load_v2():
    f = KB / "mech-terminology-v2.json"
    data = json.loads(f.read_text())
    return data.get("terms", []), data.get("extracted_extras", [])


def load_v3():
    f = KB / "mech-terminology-v3.json"
    data = json.loads(f.read_text())
    return data.get("terms", []), data.get("extracted_extras", [])


def map_category(cat):
    return CAT_MAP.get(cat, cat)


def merge_terms(v2_terms, v3_terms):
    """Merge v2 terms with v3 descriptions"""
    # Build v3 lookup by English term
    v3_by_en = {}
    for t in v3_terms:
        en = t.get("en", "").lower().strip()
        if en:
            v3_by_en[en] = t

    merged = []
    for t in v2_terms:
        entry = {
            "en": t.get("en", ""),
            "zh": t.get("zh", ""),
            "category": map_category(t.get("category", "未分类")),
            "source": t.get("source", "机械工程术语表 v2"),
        }
        # Use v3 description if v2 lacks definition
        en_lower = t.get("en", "").lower().strip()
        if en_lower in v3_by_en:
            v3t = v3_by_en[en_lower]
            entry["description"] = v3t.get("description", t.get("definition", ""))
        else:
            entry["description"] = t.get("definition", "")
        merged.append(entry)
    return merged


def merge_extras(v2_extras, v3_extras):
    """Combine extras, deduplicate by English term"""
    seen = set()
    merged = []
    for items in (v3_extras, v2_extras):  # v3 extras first (larger)
        for t in items:
            en = t.get("en", "").lower().strip()
            if en and en not in seen:
                seen.add(en)
                merged.append({
                    "en": t.get("en", ""),
                    "zh": t.get("zh", ""),
                    "category": map_category(t.get("category", "未分类")),
                    "description": t.get("description", t.get("definition", "")),
                    "source": t.get("source", "机械工程术语表 v3"),
                })
    return merged


def main():
    v2_terms, v2_extras = load_v2()
    v3_terms, v3_extras = load_v3()
    print(f"v2: {len(v2_terms)} terms + {len(v2_extras)} extras", file=sys.stderr)
    print(f"v3: {len(v3_terms)} terms + {len(v3_extras)} extras", file=sys.stderr)

    merged_terms = merge_terms(v2_terms, v3_terms)
    merged_extras = merge_extras(v2_extras, v3_extras)

    desc_count = sum(1 for t in merged_terms if t.get("description"))
    zh_count = sum(1 for t in merged_terms if t.get("zh"))
    cat_count = sum(1 for t in merged_terms if t.get("category") and t["category"] != "未分类")

    print(f"\nMerged: {len(merged_terms)} terms + {len(merged_extras)} extras = {len(merged_terms)+len(merged_extras)} total", file=sys.stderr)
    print(f"  Terms with description: {desc_count}/{len(merged_terms)} ({desc_count/len(merged_terms)*100:.1f}%)", file=sys.stderr)
    print(f"  Terms with zh: {zh_count}/{len(merged_terms)} ({zh_count/len(merged_terms)*100:.1f}%)", file=sys.stderr)
    print(f"  Terms classified: {cat_count}/{len(merged_terms)} ({cat_count/len(merged_terms)*100:.1f}%)", file=sys.stderr)

    output = {
        "meta": {
            "version": "4",
            "source": "merge v2 + v3",
            "created": "2026-05-18",
            "total_terms": len(merged_terms),
            "total_extras": len(merged_extras),
        },
        "terms": merged_terms,
        "extracted_extras": merged_extras,
    }

    out_path = KB / "mech-terminology-v4.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\nWritten to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
