#!/usr/bin/env python3
"""Wikipedia 机械工程词条批量采集脚本
用法: python3 wikipedia-collect.py [--depth 2] [--limit 500]
输出: ../knowledge-base/wikipedia-pages.json
"""
import json, sys, time, urllib.request, urllib.parse, argparse
from pathlib import Path

API = "https://en.wikipedia.org/w/api.php"
OUTPUT = Path(__file__).parent.parent / "knowledge-base" / "wikipedia-pages.json"

# 机械工程核心子分类 - 覆盖 catalog-index.json 的 11 个一级分类
ROOT_CATEGORIES = [
    "Mechanical_engineering",
    "Engineering_materials",
    "Strength_of_materials",
    "Mechanical_design",
    "Manufacturing",
    "Thermodynamics",
    "Fluid_mechanics",
    "Heat_transfer",
    "Mechatronics",
    "Industrial_automation",
    "Quality_control",
    "Engineering_tolerances",
    "Machine_elements",
    "Gears",
    "Bearings_(mechanical)",
    "Fasteners",
    "Engine_technology",
    "Hydraulics",
    "Pneumatics",
    "Numerical_control",
    "CAD/CAM",
    "Finite_element_method",
    "Robotics",
    "Renewable_energy_technology",
    "Internal_combustion_engine",
    "Turbomachinery",
    "Welding",
    "Casting_(manufacturing)",
    "Forging",
    "Machining",
]

def api_call(params):
    """Call MediaWiki API with retry."""
    params["format"] = "json"
    params["origin"] = "*"
    for retry in range(3):
        try:
            url = API + "?" + urllib.parse.urlencode(params, doseq=True)
            req = urllib.request.Request(url, headers={"User-Agent": "JixieBaikeBot/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:
            if retry < 2:
                time.sleep(2 ** retry)
            else:
                print(f"  [WARN] API call failed: {e}", file=sys.stderr)
                return None

def get_category_pages(category, depth=2, seen=None):
    """Recursively get pages from a category and subcategories."""
    if seen is None:
        seen = set()
    pages = {}
    indent = "  " * (3 - depth) if depth < 3 else "  "

    cmtitle = f"Category:{category}"
    if cmtitle in seen:
        return pages
    seen.add(cmtitle)

    print(f"{indent}📂 {category}", file=sys.stderr)

    cmcontinue = None
    subcats = []
    batch = 0
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": cmtitle,
            "cmlimit": "max",
            "cmtype": "page|subcat",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        data = api_call(params)
        if not data:
            break
        for m in data.get("query", {}).get("categorymembers", []):
            if m["ns"] == 0:  # Main namespace pages
                pages[m["title"]] = {"title": m["title"], "pageid": m["pageid"]}
            elif m["ns"] == 14:  # Subcategories
                subcats.append(m["title"].replace("Category:", ""))
        if "continue" in data and "cmcontinue" in data["continue"]:
            cmcontinue = data["continue"]["cmcontinue"]
            batch += 1
            if batch % 5 == 0:
                time.sleep(0.5)
        else:
            break

    print(f"{indent}  → {len(pages)} pages, {len(subcats)} subcats", file=sys.stderr)

    if depth > 1:
        for sc in subcats[:10]:  # Limit subcats to avoid explosion
            subpages = get_category_pages(sc, depth - 1, seen)
            for k, v in subpages.items():
                if k not in pages:
                    pages[k] = v
    return pages

def get_page_extracts(titles_batch):
    """Get extracts for a batch of page titles."""
    params = {
        "action": "query",
        "titles": "|".join(titles_batch),
        "prop": "extracts|info",
        "exintro": True,
        "explaintext": True,
        "exchars": 500,
        "inprop": "url",
        "redirects": 1,
    }
    data = api_call(params)
    if not data:
        return {}
    results = {}
    for pid, page in data.get("query", {}).get("pages", {}).items():
        if int(pid) < 0:
            continue
        results[page["title"]] = {
            "title": page["title"],
            "pageid": page["pageid"],
            "fullurl": page.get("fullurl", f"https://en.wikipedia.org/wiki/{urllib.parse.quote(page['title'].replace(' ', '_'))}"),
            "extract": page.get("extract", ""),
        }
    return results


def main():
    ap = argparse.ArgumentParser(description="Collect Wikipedia mechanical engineering pages")
    ap.add_argument("--depth", type=int, default=2, help="Category recursion depth (default: 2)")
    ap.add_argument("--limit", type=int, default=500, help="Max pages to collect (default: 500)")
    args = ap.parse_args()

    print(f"Wikipedia 机械工程词条采集 — 深度={args.depth}, 上限={args.limit}", file=sys.stderr)
    print(f"根分类数: {len(ROOT_CATEGORIES)}", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    all_pages = {}
    for i, cat in enumerate(ROOT_CATEGORIES):
        if len(all_pages) >= args.limit:
            break
        pages = get_category_pages(cat, depth=2)
        for k, v in pages.items():
            if k not in all_pages:
                all_pages[k] = v
        time.sleep(0.5)

    # Deduplicate and limit
    unique_titles = list(dict.fromkeys(all_pages.keys()))[:args.limit]
    print(f"\n去重后: {len(unique_titles)} 个词条", file=sys.stderr)
    print("开始获取摘要内容...", file=sys.stderr)

    # Get extracts in batches
    BATCH = 50
    all_results = {}
    for i in range(0, len(unique_titles), BATCH):
        batch = unique_titles[i:i+BATCH]
        extracts = get_page_extracts(batch)
        all_results.update(extracts)
        print(f"  [{i//BATCH + 1}/{(len(unique_titles)-1)//BATCH + 1}] {len(extracts)} pages", file=sys.stderr)
        time.sleep(0.5)

    # Categorize pages by our taxonomy
    categorized = {cat: [] for cat in ROOT_CATEGORIES}
    uncategorized = []
    for title, info in all_results.items():
        t_lower = title.lower()
        matched = False
        for cat in ROOT_CATEGORIES:
            cat_keywords = cat.lower().replace("_", " ").replace("(mechanical)", "").strip()
            cat_words = set(cat_keywords.split())
            title_words = set(t_lower.replace("(", "").replace(")", "").split())
            if cat_words and cat_words.intersection(title_words):
                pass  # Simple keyword match, but we'll just use first match
            # Simpler: first category to match by keyword wins
        # Assign to first matching category
        for cat in ROOT_CATEGORIES:
            cat_keywords = cat.lower().replace("_", " ").split()
            if any(kw in t_lower for kw in cat_keywords if len(kw) > 3):
                categorized[cat].append(info)
                matched = True
                break
        if not matched:
            # Default: mechanical engineering
            categorized["Mechanical_engineering"].append(info)

    output = {
        "meta": {
            "source": "Wikipedia (en)",
            "api": API,
            "collected": "2026-05-18",
            "total_pages": len(all_results),
            "depth": args.depth,
        },
        "categories": {cat: pages for cat, pages in categorized.items() if pages},
        "all_pages": list(all_results.values()),
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\n✅ 完成！保存到: {OUTPUT}", file=sys.stderr)
    print(f"   总词条数: {len(all_results)}", file=sys.stderr)

if __name__ == "__main__":
    main()
