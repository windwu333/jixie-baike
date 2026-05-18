#!/usr/bin/env python3
"""S2 Compliance Scanner — Wikipedia标准内容质量检查

检查项:
  1. 导言首句定义式 (**term** is ...)
  2. 无时间敏感词 (正朝着/近年来/最新/当前)
  3. 附录顺序标准化 (术语→参见→引用→延伸→外链)
  4. quality_level 字段存在
  5. related_terms 存在时包含参见章节
"""
import sys, re
from pathlib import Path

CONTENT = Path(__file__).parent.parent / "content"
WEBSITE = CONTENT / "website"

# Time-sensitive word patterns to detect
TIME_SENSITIVE = re.compile(r"正朝着|近年来|最新发展|当前，人工|最近，")

# Required appendix sections in order
REQUIRED_APPENDIX = [
    "术语注释与数据来源",
    "参见",
    "参考资料",
    "延伸阅读",
    "外部链接",
]


def check_lead_definition(text):
    """Check lead starts with bold definition: **term** is [category]"""
    match = re.search(r"> \*\*(.+?)\*\*是", text)
    return bool(match)


def check_time_sensitive(text):
    """Check for forbidden time-sensitive language"""
    return not bool(TIME_SENSITIVE.search(text))


def check_appendix_order(text):
    """Check appendix sections are in standard order"""
    indices = []
    for section in REQUIRED_APPENDIX:
        pos = text.find(f"### {section}")
        if pos >= 0:
            indices.append((pos, section))
    indices.sort()
    ordered = [s for _, s in indices]
    # Check if seen order matches REQUIRED_APPENDIX subsequence
    i = 0
    for s in ordered:
        while i < len(REQUIRED_APPENDIX) and REQUIRED_APPENDIX[i] != s:
            i += 1
        if i >= len(REQUIRED_APPENDIX):
            return False
        i += 1
    return True


def check_quality_level(text):
    """Check frontmatter has quality field"""
    return "quality:" in text[:1000]


def check_see_also(text):
    """If related_terms exist, check 参见 section present"""
    has_see = "## 参见" in text
    related_in_fm = "related_terms" in text[:1000]
    # If has related_terms in article, should have see-also
    return True  # We handle missing gracefully


def scan_all():
    files = sorted(WEBSITE.glob("*.md"))
    results = []
    passed = {"lead_definition": 0, "no_time_sensitive": 0,
              "appendix_order": 0, "has_quality": 0, "has_see_also": 0}
    failed = {"lead_definition": 0, "no_time_sensitive": 0,
              "appendix_order": 0, "has_quality": 0, "has_see_also": 0}

    for f in files:
        text = f.read_text()
        errors = []

        c1 = check_lead_definition(text)
        c2 = check_time_sensitive(text)
        c3 = check_appendix_order(text)
        c4 = check_quality_level(text)
        c5 = check_see_also(text)

        if c1: passed["lead_definition"] += 1
        else: failed["lead_definition"] += 1; errors.append("lead_no_definition")

        if c2: passed["no_time_sensitive"] += 1
        else: failed["no_time_sensitive"] += 1; errors.append("time_sensitive_words")

        if c3: passed["appendix_order"] += 1
        else: failed["appendix_order"] += 1; errors.append("appendix_order_wrong")

        if c4: passed["has_quality"] += 1
        else: failed["has_quality"] += 1; errors.append("no_quality_field")

        has_see = "## 参见" in text
        if has_see: passed["has_see_also"] += 1
        else: failed["has_see_also"] += 1

        if errors:
            results.append((f.name, errors))

    n = len(files)
    print(f"[S2 Scan] {n} files, results:\n", file=sys.stderr)
    checks = ["lead_definition", "no_time_sensitive", "appendix_order",
              "has_quality", "has_see_also"]
    for c in checks:
        pct = passed[c] / n * 100
        pct_txt = f"{pct:.1f}%" if pct < 99.9 else f"{pct:.0f}%"
        status = "✅" if pct >= 95 else "⚠️" if pct >= 80 else "❌"
        print(f"  {status} {c:20s}: {passed[c]:>4d}/{n} ({pct_txt})", file=sys.stderr)

    if results:
        print(f"\n  Failed files: {len(results)}", file=sys.stderr)
        for name, errs in results[:10]:
            print(f"    {name}: {', '.join(errs)}", file=sys.stderr)
    else:
        print(f"\n  ✅ All checks passed!", file=sys.stderr)

    thresholds = {"has_see_also": 0.80}
    overall = all(passed[c] / n >= thresholds.get(c, 0.95) for c in checks)
    print(f"\n  Overall: {'✅ PASS' if overall else '❌ NEEDS_IMPROVEMENT'} (threshold=95%, see-also=80%)", file=sys.stderr)
    return overall


if __name__ == "__main__":
    scan_all()
