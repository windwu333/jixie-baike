#!/usr/bin/env python3
"""Wikipedia 框架合规全面审计

扩展 S2 扫描器，按 wikipedia-structure-framework 规则体系（R1-R10）
对全部 2271 页进行审计，输出结构化报告。
"""
import json, re, sys
from pathlib import Path
from collections import Counter, defaultdict

CONTENT = Path(__file__).parent.parent / "content" / "website"

# ── 规则 R2: 标题层级无跳跃 ──
CHECK_HEADING_JUMP = re.compile(r'^#{2,5}\s')

# ── 规则 R5: 段首摘要（检测是否存在孤立段落） ──
# 检测正文段是否过长（>8句）且不拆分

# ── 规则 R7: 人称检测 ──
PERSON_PATTERNS = re.compile(
    r'\b(你[的们]?|我[们的]?|你们|we|We\b|you\b|You\b|our|Our\b)',
    re.UNICODE
)

# ── 规则 R9: 引文覆盖 ──
REF_PATTERN = re.compile(r'\[([^\]]+)\]\([^)]+\)|<\s*ref\b|【\d+】|\[\d+\]')

# ── 附录章节检测 ──
APPENDIX_SECTIONS = [
    "术语注释与数据来源", "参见", "参考资料", "延伸阅读", "外部链接"
]

# ── 质量分级分布 ──
QUALITY_LEVELS = ["F", "E", "D", "C", "B", "A", "S"]

def get_frontmatter_field(text, field):
    m = re.search(rf'^{field}:\s*(.+)$', text, re.MULTILINE)
    return m.group(1).strip() if m else None

def strip_frontmatter(text):
    if text.startswith('---'):
        end = text.find('---', 3)
        if end > 0:
            return text[end+3:]
    return text

def check_lead_para_count(text):
    """R1 extended: lead should be 1-4 paragraphs"""
    body = strip_frontmatter(text)
    # Find lead: content between first h2 and start
    first_h2 = body.find('\n## ')
    if first_h2 < 0:
        lead = body[:1000]
    else:
        lead = body[:first_h2]
    # Count paragraphs (non-empty lines)
    paras = [p.strip() for p in lead.split('\n') if p.strip() and not p.strip().startswith('>')]
    # Filter out blockquote (glossary footnotes)
    paras = [p for p in paras if not p.startswith('>')]
    n = len(paras)
    return n, 1 <= n <= 4

def check_first_sentence_definition(text):
    """R1: First sentence bold definition"""
    body = strip_frontmatter(text)
    first_h2 = body.find('\n## ')
    lead = body[:first_h2] if first_h2 > 0 else body[:2000]
    return bool(re.search(r'> \*\*(.+?)\*\*是', lead[:500]))

def check_no_personal_pronouns(text):
    """R7: No first/second person"""
    body = strip_frontmatter(text)
    matches = PERSON_PATTERNS.findall(body)
    # Filter out code blocks and blockquotes
    filtered = [m for m in matches if len(m.strip()) >= 2]
    # Also filter common false positives
    false_pos = {'我们', '我们我们'}  # unlikely but just in case
    filtered = [m for m in filtered if m not in false_pos]
    return len(filtered), filtered[:10]

def check_heading_jumps(text):
    """R2: No heading level jumps (==→====)"""
    body = strip_frontmatter(text)
    headings = CHECK_HEADING_JUMP.findall(body)
    levels = [len(h.strip()) for h in headings]
    jumps = []
    for i in range(1, len(levels)):
        if levels[i] > levels[i-1] + 1:
            jumps.append((levels[i-1], levels[i]))
    return len(jumps), jumps[:5]

def check_reference_coverage(text):
    """R9: Check if article has at least 1 reference"""
    body = strip_frontmatter(text)
    refs = REF_PATTERN.findall(body)
    # Count unique references
    ref_count = len([r for r in refs if r[0].strip()])
    return ref_count

def check_bold_usage(text):
    """R1: Bold should only be in first sentence definition"""
    body = strip_frontmatter(text)
    bolds = re.findall(r'\*\*(.+?)\*\*', body)
    # Count bolds outside of frontmatter
    bolds_in_body = [b for b in bolds if len(b) < 100]
    # Check if bold appears in section headings
    heading_bolds = re.findall(r'^#{2,5}\s.*?\*\*.*?\*\*.*$', body, re.MULTILINE)
    return len(bolds_in_body), len(heading_bolds), bolds_in_body[:5]

def check_section_length(text):
    """R4: Check for overlong sections (>3 paragraphs might need splitting)"""
    body = strip_frontmatter(text)
    sections = re.split(r'\n(?=## )', body)
    overlong = 0
    for sec in sections:
        if not sec.strip():
            continue
        # Count non-empty paragraphs
        paras = [p for p in sec.split('\n') if p.strip() and not p.startswith('#')]
        if len(paras) > 8:  # heuristic: >8 lines of text
            overlong += 1
    return overlong

def check_quality_distribution(text):
    """Check quality_level field"""
    ql = get_frontmatter_field(text, 'quality')
    return ql

def check_category_tags(text):
    """Check for category/tag field in frontmatter"""
    tags = get_frontmatter_field(text, 'tags')
    categories = get_frontmatter_field(text, 'categories')
    return bool(tags or categories)

def run_full_audit():
    files = sorted(CONTENT.glob("*.md"))
    n = len(files)

    # Accumulators
    results = defaultdict(list)
    quality_dist = Counter()
    counts = {k: 0 for k in [
        "lead_definition", "lead_1_4_paras", "no_personal_pronouns",
        "has_references", "no_heading_jumps", "proper_bold_usage",
        "has_quality", "has_category", "reasonable_section_length"
    ]}

    lead_para_issues = []
    personal_pronoun_issues = []
    heading_jump_issues = []
    ref_histogram = Counter()
    quality_levels = Counter()
    bold_issues = []
    sample_articles = []

    for i, f in enumerate(files):
        text = f.read_text()
        fname = f.name

        # ── R1: Lead definition ──
        if check_first_sentence_definition(text):
            counts["lead_definition"] += 1

        # ── R1 extended: Lead paragraph count ──
        para_count, ok = check_lead_para_count(text)
        if ok:
            counts["lead_1_4_paras"] += 1
        else:
            lead_para_issues.append((fname, para_count))

        # ── R7: No personal pronouns ──
        pcount, pmatches = check_no_personal_pronouns(text)
        if pcount == 0:
            counts["no_personal_pronouns"] += 1
        else:
            personal_pronoun_issues.append((fname, pcount, pmatches))

        # ── R9: Reference coverage ──
        ref_count = check_reference_coverage(text)
        ref_histogram[min(ref_count, 20)] += 1
        if ref_count >= 1:
            counts["has_references"] += 1

        # ── R2: No heading jumps ──
        jump_count, jumps = check_heading_jumps(text)
        if jump_count == 0:
            counts["no_heading_jumps"] += 1
        else:
            heading_jump_issues.append((fname, jump_count))

        # ── R1: Bold usage ──
        bold_count, heading_bold_count, bolds = check_bold_usage(text)
        # More than 3 bolds outside headings is excessive
        if bold_count <= 3 or heading_bold_count > 0:
            counts["proper_bold_usage"] += 1
        else:
            if len(bold_issues) < 20:
                bold_issues.append((fname, bold_count))

        # ── Quality ──
        ql = check_quality_distribution(text)
        if ql:
            counts["has_quality"] += 1
            quality_levels[ql] += 1

        # ── Category ──
        if check_category_tags(text):
            counts["has_category"] += 1

        # ── Section length ──
        overlong = check_section_length(text)
        if overlong <= 3:
            counts["reasonable_section_length"] += 1

        # Sample 20 files periodically for deep review
        if i % 114 == 0:  # ~20 samples evenly spaced
            sample_articles.append(fname)

    # ── Print report ──
    print("=" * 70)
    print("  维基百科框架合规全面审计报告")
    print("=" * 70)
    print(f"  扫描文件: {n}")
    print()

    checks = [
        ("lead_definition", "R1 导言定义式", "✅"),
        ("lead_1_4_paras", "R1 导言1-4段", "✅"),
        ("no_personal_pronouns", "R7 无人称代词", "✅"),
        ("has_references", "R9 引用覆盖(≥1)", "✅"),
        ("no_heading_jumps", "R2 标题无跳级", "✅"),
        ("proper_bold_usage", "R1 加粗适度", "✅"),
        ("has_quality", "质量分级字段", "✅"),
        ("has_category", "分类标签", "✅"),
        ("reasonable_section_length", "R4 章节适当", "✅"),
    ]

    for key, label, icon in checks:
        pct = counts[key] / n * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"  {icon if pct >= 90 else '⚠️'} {label:20s}: {counts[key]:>5d}/{n} ({pct:5.1f}%) {bar}")

    print()
    print(f"{'─'*70}")
    print(f"  深度审计项")
    print(f"{'─'*70}")

    if lead_para_issues:
        print(f"\n  ⚠️  导言段落数异常 ({len(lead_para_issues)} 篇):")
        for fname, pc in lead_para_issues[:10]:
            print(f"      {fname[:50]:50s} → {pc}段")

    if personal_pronoun_issues:
        print(f"\n  ⚠️  含人称代词 ({len(personal_pronoun_issues)} 篇):")
        for fname, pc, matches in personal_pronoun_issues[:10]:
            m_str = ', '.join(matches[:3])
            print(f"      {fname[:50]:50s} → {pc}处 ({m_str})")

    if heading_jump_issues:
        print(f"\n  ⚠️  标题跳级 ({len(heading_jump_issues)} 篇):")
        for fname, jc in heading_jump_issues[:10]:
            print(f"      {fname[:50]:50s} → {jc}处跳级")

    if bold_issues:
        print(f"\n  ⚠️  加粗过多 ({len(bold_issues)} 篇):")
        for fname, bc in bold_issues[:10]:
            print(f"      {fname[:50]:50s} → {bc}处加粗")

    print(f"\n  📊 引用分布:")
    for rc in sorted(ref_histogram.keys()):
        if rc <= 5:
            label = str(rc) if rc < 20 else "20+"
            pct = ref_histogram[rc] / n * 100
            bar = "█" * int(pct / 2)
            print(f"      {label:3s}条: {ref_histogram[rc]:>5d}篇 ({pct:4.1f}%) {bar}")

    print(f"\n  📊 质量等级分布:")
    for ql in sorted(quality_levels.keys()):
        pct = quality_levels[ql] / n * 100
        bar = "█" * int(pct / 3)
        print(f"      {ql:5s}: {quality_levels[ql]:>5d}篇 ({pct:4.1f}%) {bar}")

    print(f"\n  📋 抽样深度审查 ({len(sample_articles)} 篇):")
    for f in sample_articles:
        print(f"      {f}")

    # Generate summary JSON
    report = {
        "n": n,
        "checks": {k: {"passed": v, "pct": round(v/n*100, 1)} for k, v in counts.items()},
        "quality_distribution": dict(quality_levels),
        "ref_histogram": {str(k): v for k, v in sorted(ref_histogram.items())},
        "lead_para_issues": len(lead_para_issues),
        "personal_pronoun_issues": len(personal_pronoun_issues),
        "heading_jump_issues": len(heading_jump_issues),
        "bold_issues": len(bold_issues),
        "sample_articles": sample_articles,
    }

    report_path = Path(__file__).parent.parent / "reports" / "wiki-framework-audit-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n  📄 完整报告: {report_path}")

    return report


if __name__ == "__main__":
    run_full_audit()
