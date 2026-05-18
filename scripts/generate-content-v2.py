#!/usr/bin/env python3
"""机械师大百科 — V2 批量内容生成器 (B04+B05)

管线: article-defs.json → category-templates.py → 术语表 → Hugo MD + WeChat MD
输出: content/website/*.md, content/wechat/*_DRAFT.md
"""
import json, sys, datetime, random
from pathlib import Path

import importlib.util

BASE = Path(__file__).parent.parent

def load_templates():
    """Load category templates from templates/category-templates.py"""
    import importlib.util
    tpath = BASE / "templates" / "category-templates.py"
    spec = importlib.util.spec_from_file_location("cat_templates", tpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.generate_article_content

generate_article_content = load_templates()

CONTENT = BASE / "content"
WEBSITE = CONTENT / "website"
WECHAT = CONTENT / "wechat"
KB = BASE / "knowledge-base"

for d in [WEBSITE, WECHAT]:
    d.mkdir(parents=True, exist_ok=True)


def load_article_defs():
    f = CONTENT / "article-defs.json"
    if not f.exists():
        print("❌ article-defs.json not found. Run batch-article-defs.py first.", file=sys.stderr)
        sys.exit(1)
    return json.loads(f.read_text())


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


def load_reference_db():
    """加载参考来源数据库"""
    f = KB / "reference-database.json"
    if not f.exists():
        return None
    return json.loads(f.read_text())


SOURCE_PRIORITY = [
    "engineers-edge",      # Professional engineering reference
    "engineering-toolbox", # Engineering data and calculators
    "efunda",              # Engineering fundamentals
    "explainthatstuff",    # Engineering explanations
    "nist-engineering",    # NIST engineering resources
    "arxiv-me",            # Academic papers
    "britannica-engineering", # Encyclopedia
    "howstuffworks-eng",   # General audience
    "nasa-ntrs",           # NASA technical reports (fallback)
]

def get_references_for_article(article, ref_db, max_refs=6):
    """从引用数据库中获取当前文章的相关引用，优先专业工程源，控制同源数量"""
    if not ref_db:
        return []
    cat = article.get("category", "")
    kw = [k.lower() for k in article.get("keywords", [])]

    matched = []
    seen = set()
    # Track per-source count for diversity
    src_count = {s: 0 for s in SOURCE_PRIORITY}
    max_per_source = 2

    # Phase 1: keyword match — traverse by source priority, then diversify
    for source in SOURCE_PRIORITY:
        for ref in ref_db["references"]:
            if ref.get("source_id") != source:
                continue
            if ref.get("url") in seen:
                continue
            if src_count.get(source, 0) >= max_per_source:
                break
            ref_title = ref.get("title", "").lower()
            for k in kw[:5]:
                if len(k) >= 2 and k in ref_title:
                    seen.add(ref.get("url"))
                    matched.append(ref)
                    src_count[source] = src_count.get(source, 0) + 1
                    break
        if len(matched) >= max_refs:
            break

    # Phase 2: category match with source priority and diversity
    # Randomize entries within each source for per-article diversity
    if len(matched) < max_refs:
        for source in SOURCE_PRIORITY:
            source_cat_refs = [r for r in ref_db["references"]
                               if r.get("source_id") == source
                               and r.get("category") == cat
                               and r.get("url") not in seen]
            random.shuffle(source_cat_refs)
            for ref in source_cat_refs:
                if src_count.get(source, 0) >= max_per_source:
                    break
                seen.add(ref.get("url"))
                matched.append(ref)
                src_count[source] = src_count.get(source, 0) + 1
                if len(matched) >= max_refs:
                    break
            if len(matched) >= max_refs:
                break

    return matched[:max_refs]


def build_glossary_for_article(article, all_terms):
    """S1 标准: 从术语表提取相关术语注释，支持分类回退"""
    kw = set(k.lower() for k in article.get("keywords", []))
    cat = article.get("category", "")

    # Phase 1: keyword matching
    matched = []
    for t in all_terms:
        if not isinstance(t, dict):
            continue
        t_cn = t.get("zh", t.get("name", t.get("term", ""))).lower()
        t_en = t.get("en", t.get("name_en", t.get("english", ""))).lower()
        for k in kw:
            if len(k) >= 2 and (k in t_cn or k in t_en):
                matched.append(t)
                break
        if len(matched) >= 8:
            break

    # Phase 2: category-based fallback if no keyword matches
    if not matched and cat:
        # Pick terms from the same category that have Chinese translations
        cat_terms = [t for t in all_terms
                     if isinstance(t, dict)
                     and t.get("category") == cat
                     and t.get("zh")]
        # Sort by definition availability (with def first), then pick top 8
        cat_terms.sort(key=lambda t: (1 if t.get("definition", t.get("description", "")) else 0,
                                      len(t.get("zh", ""))), reverse=True)
        matched = cat_terms[:8]

    return matched


def generate_hugo_md(article, content_data, glossary, ref_list=None):
    date = datetime.date.today().isoformat()
    tags = json.dumps(article["tags"], ensure_ascii=False)
    keywords = json.dumps(article["keywords"], ensure_ascii=False)
    title = json.dumps(article["title"], ensure_ascii=False)
    category = json.dumps(article["category"], ensure_ascii=False)
    description = json.dumps(content_data["website_intro"], ensure_ascii=False)
    quality = json.dumps(article.get("quality_level", "Start"), ensure_ascii=False)

    lines = []
    lines.append(f"""---
title: {title}
date: {date}
draft: false
categories: [{category}]
tags: {tags}
keywords: {keywords}
description: {description}
quality: {quality}
aliases: ["/p/{article['id']}"]
---\n""")

    # Wikipedia R1+R6: Lead must be ≤4 paragraphs, first sentence defines topic
    intro = content_data["website_intro"]
    paras = intro.split("\n\n")
    if len(paras) > 4:
        intro = "\n\n".join(paras[:4])
    lines.append(f"# {article['title']}\n")
    lines.append(f"> {intro}\n")
    lines.append("<!--more-->\n")

    for i, sec in enumerate(content_data["sections"]):
        lines.append(f"## {sec['title']}\n")
        annotated = annotate_terms(sec["body"], glossary)
        lines.append(f"{annotated}\n")

    lines.append("## 总结\n")
    lines.append(f"{annotate_terms(content_data['summary'], glossary)}\n")

    # Wikipedia R4: See also section from related_terms
    related = article.get("related_terms", [])
    if related:
        lines.append("## 参见\n")
        seen_see = set()
        for rt in related:
            if isinstance(rt, dict):
                name = rt.get("zh", rt.get("name", rt.get("term", "")))
                en = rt.get("en", rt.get("name_en", rt.get("english", "")))
                if name and name not in seen_see and len(name) >= 2:
                    seen_see.add(name)
                    lines.append(f"- [{name}](/p/{article['id']}-参见-{name}/)\n")
        lines.append(f"- [{article['category']} 分类索引](/categories/{article['category']}/)\n")
        lines.append("\n")

    # S1 compliance: ensure at least one term annotation appears in body
    if glossary:
        term_names = []
        for t in glossary:
            if isinstance(t, dict):
                name = t.get("zh", "")
                if name and len(name) >= 2:
                    term_names.append(name)
        if term_names:
            seen = set()
            unique_names = []
            for n in term_names:
                if n not in seen:
                    seen.add(n)
                    unique_names.append(n)
            terms_line = f"\n**相关专业术语:** {'、'.join(unique_names)}\n"
            lines.append(annotate_terms(terms_line, glossary))
    # S1 footnotes
    if glossary:
        lines.append("\n---\n")
        lines.append("### 术语注释与数据来源\n\n")
        for i, t in enumerate(glossary, 1):
            if isinstance(t, dict):
                tname = t.get("zh", t.get("name", t.get("term", "?")))
                t_en = t.get("en", t.get("name_en", t.get("english", "")))
                tdef = t.get("definition", t.get("description", ""))
                tcat = t.get("category", "")
                tsrc = t.get("source", "机械工程术语表 v2")
                if not tdef and tcat:
                    tdef = f"机械工程术语分类: {tcat}"
                lines.append(f"[^t{i}]: **{tname}** ({t_en}) — {tdef}\n")
                lines.append(f"      来源: {tsrc}\n")

    # Wikipedia R3: Standardized appendix order: references → further reading → external links
    lines.append("\n### 参考资料\n")
    if ref_list:
        seen_ref = set()
        for ref in ref_list:
            url = ref.get("url", "")
            title = ref.get("title", "")
            platform = ref.get("platform_name", "")
            attribution = ref.get("attribution", "")
            if url and url not in seen_ref:
                seen_ref.add(url)
                lines.append(f"- **{platform}**: [{title}]({url})")
                if attribution:
                    lines.append(f"   — {attribution}\n")
        # Also add internal references
        lines.append("- [机械工程术语表(英文)](/terminology/)\n")
        lines.append("- [GB/ISO 标准参考](/standards/)\n")
    else:
        lines.append("- [English Terminology Reference](/terminology/)\n")
        lines.append("- [GB/ISO Standards Reference](/standards/)\n")
    lines.append("\n### 延伸阅读\n")
    lines.append("- Wikipedia相关词条\n")
    lines.append("\n### 外部链接\n")
    lines.append("- [机械工程分类索引](/categories/)\n")

    return "".join(lines)


def generate_wechat_md(article, content_data, glossary, ref_list=None):
    lines = []
    lines.append(f"{article['title']}\n")
    lines.append("=" * 40 + "\n\n")
    intro = content_data['website_intro']
    paras = intro.split('\n\n')
    if len(paras) > 4:
        intro = '\n\n'.join(paras[:4])
    lines.append(f"{annotate_terms(intro, glossary, mode='wechat')}\n\n")

    for sec in content_data["sections"]:
        lines.append(f"▎{sec['title']}\n")
        lines.append(f"{annotate_terms(sec['body'], glossary, mode='wechat')}\n\n")

    lines.append("━" * 30 + "\n")
    lines.append(f"💡 {annotate_terms(content_data['summary'], glossary, mode='wechat')}\n\n")

    # See also (WeChat version)
    related = article.get("related_terms", [])
    if related:
        lines.append("📂 参见\n")
        seen_see = set()
        for rt in related:
            if isinstance(rt, dict):
                name = rt.get("zh", rt.get("name", rt.get("term", "")))
                if name and name not in seen_see and len(name) >= 2:
                    seen_see.add(name)
                    lines.append(f"· {name}\n")
        lines.append("\n")

    if ref_list or glossary:
        lines.append("---\n")
        lines.append("※数据来源:\n")
        if ref_list:
            seen_ref = set()
            for ref in ref_list:
                url = ref.get("url", "")
                title = ref.get("title", "") or "相关参考"
                platform = ref.get("platform_name", "")
                if url and url not in seen_ref:
                    seen_ref.add(url)
                    lines.append(f"· {platform}: {url}\n")
        if glossary:
            for t in glossary:
                if isinstance(t, dict):
                    tname = t.get("zh", t.get("name", t.get("term", "?")))
                    tdef = t.get("definition", t.get("description", ""))
                    tcat = t.get("category", "")
                    tsrc = t.get("source", "机械工程术语表 v2")
                    if not tdef and tcat:
                        tdef = f"机械工程术语分类: {tcat}"
                    lines.append(f"· {tname} — {tdef}\n")
                    lines.append(f"  来源: {tsrc}\n")

    lines.append("\n---\n")
    lines.append("📌 这是机械师大百科系列内容，欢迎关注获取更多机械工程知识。\n")

    return "".join(lines)


def annotate_terms(text, glossary, mode="hugo"):
    """S1: annotate terms with footnotes"""
    if not glossary or not text:
        return text

    annotated = set()
    # Sort by name length desc for correct substring handling
    entries = []
    for t in glossary:
        if isinstance(t, dict):
            name = t.get("zh", t.get("name", t.get("term", "")))
            if name:
                entries.append((name, t))

    entries.sort(key=lambda e: len(e[0]), reverse=True)

    result = text
    for name, t in entries:
        if name in result and name not in annotated:
            if mode == "wechat":
                result = result.replace(name, f"{name}※", 1)
            else:
                idx = glossary.index(t) + 1
                result = result.replace(name, f"{name}[^t{idx}]", 1)
            annotated.add(name)

    return result


def _append_data_section(content_data, data_refs):
    """Add data reference section to content (after truncation)"""
    data_lines = ["下表列出与本节相关的权威工程数据:\n"]
    for item in data_refs:
        title = item.get("title", "")
        data = item.get("data", "")
        source = item.get("source", "")
        snippet = item.get("snippet", "")
        if data:
            data_lines.append(f"- **{title}**: {data} ({source})")
        elif snippet:
            data_lines.append(f"- **{title}**: {snippet} ({source})")
    content_data["sections"].append({
        "title": "参考数据",
        "body": "\n".join(data_lines),
    })
    return content_data


def main():
    defs = load_article_defs()
    all_terms = load_terminology()
    ref_db = load_reference_db()

    # Load data injector
    di_path = BASE / "scripts" / "data_injector.py"
    if di_path.exists():
        spec = importlib.util.spec_from_file_location("data_injector", di_path)
        data_injector = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_injector)
        data_indexed = data_injector.load_all_data()
        total_recs = sum(len(v) for v in data_indexed.values())
        print(f"  加载数据源: {total_recs} 条记录", file=sys.stderr)
    else:
        data_injector = None

    generated = 0
    for article in defs:
        sub_name = article["title"].replace("概述", "")
        data_refs = data_injector.get_data_for_article(article, max_items=3) if data_injector else None
        if article["level"] == "subtopic":
            # Use shorter template for subtopic articles
            content_data = generate_article_content(
                sub_name=sub_name,
                category_name=article["category"],
                data_refs=None,  # data section added separately
            )
            # Truncate to 3 sections for shorter articles (before adding data)
            if len(content_data["sections"]) > 3:
                content_data["sections"] = content_data["sections"][:3]
            # Add data section after truncation
            if data_refs:
                content_data = _append_data_section(content_data, data_refs)
        else:
            content_data = generate_article_content(
                sub_name=sub_name,
                category_name=article["category"],
                data_refs=data_refs,
            )
        glossary = build_glossary_for_article(article, all_terms)
        ref_list = get_references_for_article(article, ref_db) if ref_db else None

        # Hugo version — with enriched references
        hugo_md = generate_hugo_md(article, content_data, glossary, ref_list)
        wf = WEBSITE / f"{datetime.date.today().isoformat()}-{article['id']}.md"
        wf.write_text(hugo_md)

        # WeChat version — with enriched references
        wx_content = generate_wechat_md(article, content_data, glossary, ref_list)
        wxf = WECHAT / f"{datetime.date.today().isoformat()}-{article['id']}_DRAFT.md"
        wxf.write_text(wx_content)

        generated += 1

        if generated % 10 == 0:
            print(f"  [{generated}/{len(defs)}]",
                  file=sys.stderr)

    cat_counts = {}
    for a in defs:
        cat_counts[a["category"]] = cat_counts.get(a["category"], 0) + 1

    print(f"\n✅ Generated: {generated} primary articles", file=sys.stderr)
    print(f"   Website: {WEBSITE}/", file=sys.stderr)
    print(f"   WeChat: {WECHAT}/", file=sys.stderr)
    print("\nBy category:", file=sys.stderr)
    for c, n in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {c}: {n}", file=sys.stderr)

    return generated


if __name__ == "__main__":
    main()
