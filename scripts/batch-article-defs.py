#!/usr/bin/env python3
"""机械师大百科 — 批量文章定义生成器 v3 (B04+B05)

从 catalog-index.json + mech-terminology-v2 生成 1000+ 文章定义。
策略:
  1. 每个子类 1 篇主文章 (63)
  2. 每个关键词 1 篇细分文章 (325)
  3. 术语表同分类条目扩展 (~640)
  目标: 1000+ 篇
"""
import json, sys
from pathlib import Path

BASE = Path(__file__).parent.parent
KB = BASE / "knowledge-base"
RAW = BASE / "raw"

def load_catalog():
    return json.loads((KB / "catalog-index.json").read_text())

def load_terminology():
    """Return combined list of term dicts: v4 → v3 → v2, plus supplement"""
    result = []
    for ver in ("v4", "v3", "v2"):
        f = KB / f"mech-terminology-{ver}.json"
        if f.exists():
            data = json.loads(f.read_text())
            if isinstance(data, dict):
                result.extend(data.get("terms", []))
                result.extend(data.get("extracted_extras", []))
            elif isinstance(data, list):
                result.extend(data)
            break
    # Supplement: commonly missing Chinese engineering terms
    sup = KB / "mech-supplement.json"
    if sup.exists():
        result.extend(json.loads(sup.read_text()))
    return result

def load_index():
    f = RAW / ".index.json"
    if f.exists():
        idx = json.loads(f.read_text())
        return idx.get("records", [])
    return []

def extract_key_sources(records, keywords):
    matched = []
    for r in records:
        title = r.get("title", "").lower()
        if any(k.lower() in title for k in keywords):
            matched.append(r)
    return matched[:5]

def heuristic_content_length(title, keywords):
    lengthy_topics = ["热处理", "齿轮", "锻造", "焊接", "有限元", "疲劳", "振动"]
    if any(t in title for t in lengthy_topics):
        return "long"
    return "medium"

def make_tags(cat_name, sub_name):
    return [cat_name, sub_name, "机械百科"]

def assign_quality_level(content_length, level, keyword_count):
    """Auto-assign Wikipedia-style quality grade based on article attributes"""
    if level == "primary":
        if content_length == "long":
            return "B"
        else:
            return "C"
    else:  # subtopic
        if content_length == "long" or keyword_count >= 3:
            return "C"
        elif keyword_count >= 2:
            return "Start"
        else:
            return "Draft"

def get_term_val(t, *keys):
    """Get a value from a term dict trying multiple keys"""
    for k in keys:
        v = t.get(k)
        if v:
            return v
    return ""

# Terminology category → catalog category mapping
CAT_MAP = {
    "制图CAD": "机械制图与CAD",
    "力学强度": "力学与强度分析",
    "热工流体": "热工与流体",
    "机电自动化": "机械电子与自动化",
    "标准规范": "标准与规范",
    "未分类": None,  # distributed below
}

def map_term_category(term_cat, cat_terms_by_cat):
    """Map a terminology category to a catalog category name"""
    if term_cat in CAT_MAP and CAT_MAP[term_cat] is not None:
        return CAT_MAP[term_cat]
    return term_cat  # try direct match

def assign_uncategorized(term, catalog_categories):
    """Assign an '未分类' term to the best matching catalog category"""
    zh = get_term_val(term, 'zh', 'name', 'term').lower()
    en = get_term_val(term, 'en', 'name_en', 'english').lower()
    best_cat = None
    best_score = 0
    for cc in catalog_categories:
        score = 0
        cat_name_lower = cc["name"].lower()
        # Subcategory keyword matches
        for sub in cc.get("subcategories", []):
            for sk in sub.get("keywords", []):
                if sk.lower() in zh or sk.lower() in en:
                    score += 2
            # Subcategory name overlap
            sn = sub.get("name", "").lower()
            if sn in zh or sn in en:
                score += 3
        # Category name character overlap
        common = set(zh) & set(cat_name_lower)
        score += len(common) * 0.5
        # Broad English domain matching
        eng_domains = {
            "工程材料": ["material", "steel", "iron", "alloy", "metal", "ceramic", "polymer", "composite", "heat treat", "casting"],
            "力学与强度分析": ["stress", "strain", "fatigue", "vibration", "strength", "mechanics", "finite element", "load"],
            "机械设计": ["bearing", "gear", "spring", "shaft", "screw", "fastener", "design", "joint", "clutch", "brake", "coupling"],
            "制造工艺": ["machining", "welding", "forging", "casting", "molding", "manufacturing", "cutting", "drilling", "milling", "turning", "grinding", "fabrication", "assembly", "additive", "3d print"],
            "热工与流体": ["thermal", "fluid", "heat", "temperature", "thermodynamic", "hydraulic", "pneumatic"],
            "机械电子与自动化": ["sensor", "actuator", "control", "robot", "automation", "plc", "servo", "motor", "encoder"],
            "测量与质量控制": ["measurement", "inspection", "quality", "gauge", "calibration", "tolerance", "cmm"],
            "标准与规范": ["standard", "specification", "iso", "gb", "din", "astm", "code"],
            "行业应用": ["industry", "application", "agriculture", "construction", "mining", "automotive", "aerospace"],
            "动力机械与能源": ["engine", "turbine", "compressor", "pump", "power", "energy", "motor"],
            "机械制图与CAD": ["cad", "drafting", "drawing", "dimension", "tolerance", "solidworks", "autocad", "modeling", "sketch"],
        }
        for dk in eng_domains.get(cc["name"], []):
            if dk in en:
                score += 1

        if score > best_score:
            best_score = score
            best_cat = cc["name"]
    # Minimum threshold: accept any match with score >= 1
    if best_score >= 1:
        return best_cat
    # Fallback: distribute remaining unclassified terms evenly
    return None

def load_standards():
    """Load GB/ISO standards"""
    f = KB / "gb-iso-standards.json"
    if f.exists():
        data = json.loads(f.read_text())
        if isinstance(data, dict):
            return data.get("standards", [])
        return data if isinstance(data, list) else []
    return []

def generate_articles():
    catalog = load_catalog()
    all_terms = load_terminology()  # list of dicts
    records = load_index()
    standards = load_standards()

    articles = []
    article_id = 0
    used_keywords = set()  # track used titles to avoid dupes

    for cat in catalog["categories"]:
        cat_name = cat["name"]
        cat_en = cat["nameEn"]

        # Build catalog category name list for unclassified assignment
        catalog_cat_names = [c["name"] for c in catalog["categories"]]

        # Pre-filter terms by category name match (with mapping)
        cat_terms = []
        for t in all_terms:
            t_cat = str(t.get('category', '未分类')).strip().lower()
            mapped = map_term_category(t.get('category', '未分类'), None)
            if mapped == cat_name:
                cat_terms.append(t)
            elif t.get('category', '未分类') == '未分类':
                # Try assigning unclassified terms
                assigned = assign_uncategorized(t, catalog["categories"])
                if assigned == cat_name:
                    cat_terms.append(t)

        for sub in cat["subcategories"]:
            sub_id = sub["id"]
            sub_name = sub["name"]
            kw = sub.get("keywords", [])

            # --- Primary article per subcategory ---
            article_id += 1
            aid = sub_id
            a = {
                "id": aid,
                "article_no": article_id,
                "title": f"{sub_name}概述",
                "title_en": f"{sub_name} Overview",
                "category": cat_name,
                "category_en": cat_en,
                "subcategory": sub_name,
                "keywords": kw,
                "tags": make_tags(cat_name, sub_name),
                "content_length": heuristic_content_length(sub_name, kw),
                "level": "primary",
                "quality_level": assign_quality_level(heuristic_content_length(sub_name, kw), "primary", len(kw)),
                "related_terms": [t for t in all_terms
                                  if any(k.lower() in get_term_val(t, 'zh', 'name', 'term').lower()
                                         or k.lower() in get_term_val(t, 'en', 'name_en', 'english').lower()
                                         for k in kw)][:12],
                "reference_sources": extract_key_sources(records, kw),
            }
            articles.append(a)
            used_keywords.add(f"{sub_name}概述")

            # --- Sub-topic articles from ALL keywords ---
            for i, k in enumerate(kw):
                title = k
                if title in used_keywords:
                    continue
                article_id += 1
                aid_sub = f"{sub_id}-k{i}"
                a_sub = {
                    "id": aid_sub,
                    "article_no": article_id,
                    "title": title,
                    "title_en": f"{k} - Detailed Guide",
                    "category": cat_name,
                    "category_en": cat_en,
                    "subcategory": sub_name,
                    "keywords": [k] + [x for x in kw if x != k][:2],
                    "tags": make_tags(cat_name, sub_name) + [k],
                    "content_length": "short" if len(k) > 3 else "medium",
                    "level": "subtopic",
                    "quality_level": assign_quality_level("short" if len(k) > 3 else "medium", "subtopic", len([k] + [x for x in kw if x != k][:2])),
                    "related_terms": [t for t in all_terms
                                      if k.lower() in get_term_val(t, 'zh', 'name', 'term').lower()
                                      or k.lower() in get_term_val(t, 'en', 'name_en', 'english').lower()][:6],
                    "reference_sources": extract_key_sources(records, [k]),
                }
                articles.append(a_sub)
                used_keywords.add(title)

            # --- Terminology-based articles ---
            sub_terms = [t for t in cat_terms
                         if get_term_val(t, 'zh', 'name', 'term') not in used_keywords]
            for j, t in enumerate(sub_terms[:18]):
                term_name = get_term_val(t, 'zh', 'name', 'term')
                if term_name in used_keywords or not term_name:
                    continue
                article_id += 1
                aid_t = f"{sub_id}-t{j}"
                a_term = {
                    "id": aid_t,
                    "article_no": article_id,
                    "title": term_name,
                    "title_en": f"{get_term_val(t, 'en', 'name_en', 'english')} - Terminology Guide",
                    "category": cat_name,
                    "category_en": cat_en,
                    "subcategory": sub_name,
                    "keywords": [term_name] + kw[:2],
                    "tags": make_tags(cat_name, sub_name) + [term_name],
                    "content_length": "short",
                    "level": "subtopic",
                    "quality_level": "Draft",
                    "related_terms": [t],
                    "reference_sources": [],
                }
                articles.append(a_term)
                used_keywords.add(term_name)

            # --- Variant articles: 应用详解 for each short+medium term ---
            for a in list(articles):
                if a.get("subcategory") != sub_name:
                    continue
                base_title = a["title"]
                if len(base_title) < 2 or len(base_title) > 12:
                    continue
                var_title = f"{base_title}—应用详解"
                if var_title in used_keywords:
                    continue
                article_id += 1
                aid_v = f"{a['id']}-v"
                articles.append({
                    "id": aid_v, "article_no": article_id,
                    "title": var_title,
                    "title_en": f"{base_title} - Application Guide",
                    "category": cat_name, "category_en": cat_en,
                    "subcategory": sub_name,
                    "keywords": a["keywords"][:3] + ["应用"],
                    "tags": make_tags(cat_name, sub_name) + ["应用指南"],
                    "content_length": "short",
                    "level": "subtopic",
                    "quality_level": "Start",
                    "related_terms": a.get("related_terms", [])[:3],
                    "reference_sources": a.get("reference_sources", [])[:2],
                })
                used_keywords.add(var_title)

        # --- GB/ISO standards-based articles (per category, after sub loop) ---
        if standards:
            cat_standards = [s for s in standards
                             if str(s.get("category", "")).find(cat_name[:2]) >= 0]
            cat_standards = [s for s in cat_standards
                             if s.get("name", s.get("title", "")) not in used_keywords]
            for i, s in enumerate(cat_standards[:15]):
                std_name = s.get("name", s.get("title", ""))
                if not std_name:
                    continue
                article_id += 1
                aid_s = f"std-{cat_name[:4]}-{i}"
                articles.append({
                    "id": aid_s,
                    "article_no": article_id,
                    "title": std_name,
                    "title_en": s.get("english", s.get("en", f"{std_name} Standard")),
                    "category": cat_name,
                    "category_en": cat["nameEn"],
                    "subcategory": f"{cat_name}-标准",
                    "keywords": [std_name[:8], "标准", cat_name],
                    "tags": [cat_name, "标准规范", "机械百科"],
                    "content_length": "short",
                    "level": "subtopic",
                    "quality_level": "Draft",
                    "related_terms": [],
                    "reference_sources": [],
                })
                used_keywords.add(std_name)

    return articles

def main():
    articles = generate_articles()
    out = BASE / "content" / "article-defs.json"
    out.write_text(json.dumps(articles, ensure_ascii=False, indent=2))
    primary = sum(1 for a in articles if a["level"] == "primary")
    subtopic = sum(1 for a in articles if a["level"] == "subtopic")
    print(f"Articles generated: {len(articles)} ({primary} primary + {subtopic} subtopic)")
    print(f"Saved to: {out}")

    cats = {}
    for a in articles:
        cats.setdefault(a["category"], 0)
        cats[a["category"]] += 1
    print("\nBy category:")
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {c}: {n}")

if __name__ == "__main__":
    main()
