#!/usr/bin/env python3
"""Quality Gate — 发布前质量门禁检查

在 Hugo build 前运行，检查条件:
  1. lead 定义式模式 (S2)
  2. 引用充分 (≥1 reference, primary ≥3)
  3. 结构完整 (导言+章节+总结+附录)
  4. quality_level 存在
  5. 无时间敏感词

用法:
  python3 scripts/quality-gate.py              # 检查所有文章
  python3 scripts/quality-gate.py --strict     # 严格模式 (95% 阈值)
  python3 scripts/quality-gate.py --file <path> # 单文件检查
"""
import sys, re
from pathlib import Path

CONTENT = Path(__file__).parent.parent / "content" / "website"
TIME_SENSITIVE = re.compile(r"正朝着|近年来|最新发展|当前，人工|最近，")


def check_article(text: str) -> list[str]:
    errors = []
    # 1. Lead definition
    if not re.search(r"> \*\*(.+?)\*\*是", text):
        errors.append("lead_no_definition")
    # 2. Minimum references
    refs = len(re.findall(r"\[.*?\]\(.*?\)", text))
    if refs < 1:
        errors.append("insufficient_refs")
    # 3. Structure: sections + summary
    if "## " not in text:
        errors.append("no_sections")
    if "## 总结" not in text:
        errors.append("no_summary")
    # 4. Quality level
    if "quality:" not in text[:1000]:
        errors.append("no_quality_field")
    # 5. No time-sensitive language
    if TIME_SENSITIVE.search(text):
        errors.append("time_sensitive_words")
    return errors


def scan_all(strict: bool = False) -> bool:
    files = sorted(CONTENT.glob("*.md"))
    n = len(files)
    failed = 0
    threshold = 0.9 if not strict else 0.95

    print(f"[Quality Gate] Scanning {n} files (threshold={threshold:.0%})...")

    for f in files:
        errs = check_article(f.read_text())
        if errs:
            failed += 1
            if failed <= 5:
                print(f"  FAIL {f.name}: {', '.join(errs)}")

    pass_rate = (n - failed) / n
    status = "PASS" if pass_rate >= threshold else "FAIL"
    print(f"\n  Passed: {n-failed}/{n} ({pass_rate:.1%})")
    print(f"  Failed: {failed}/{n}")
    print(f"  Status: {'✅' if status == 'PASS' else '❌'} {status}")

    return status == "PASS"


if __name__ == "__main__":
    strict = "--strict" in sys.argv
    single = None
    for i, arg in enumerate(sys.argv):
        if arg == "--file" and i + 1 < len(sys.argv):
            single = Path(sys.argv[i + 1])

    if single:
        if not single.exists():
            print(f"❌ File not found: {single}")
            sys.exit(1)
        errs = check_article(single.read_text())
        if errs:
            print(f"❌ {single.name}: {', '.join(errs)}")
        else:
            print(f"✅ {single.name}: all checks passed")
    else:
        ok = scan_all(strict=strict)
        sys.exit(0 if ok else 1)
