#!/usr/bin/env python3
"""Reference Formatter — 引用格式标准化

统一所有文章中的参考资料格式为 cite-web 模板。

用法:
  python3 scripts/reference-formatter.py              # 格式化所有文章
  python3 scripts/reference-formatter.py --check      # 仅检查不修改
  python3 scripts/reference-formatter.py --file <path> # 单文件
"""
import sys, re
from pathlib import Path

CONTENT = Path(__file__).parent.parent / "content" / "website"

CITE_PATTERNS = {
    "standard": re.compile(r"- \[(.+?)\]\((.+?)\)"),         # - [Title](URL)
    "bare_url": re.compile(r"- (https?://\S+)"),              # - http://...
    "plain_text": re.compile(r"- ([^-]+?)(?:[，,]\s*(.+))?"), # - Title, source
}

CITE_WEB_TMPL = '- <cite class="cite-web">{title}</cite>'


def format_references(text: str) -> str:
    """Convert existing reference formats to cite-web template"""
    lines = text.split("\n")
    result = []
    in_refs = False

    for line in lines:
        if line.startswith("### 参考资料"):
            in_refs = True
            result.append(line)
            continue

        if in_refs:
            if line.startswith("### ") or line.startswith("---"):
                in_refs = False
                result.append(line)
                continue
            if line.startswith("- ["):
                m = CITE_PATTERNS["standard"].match(line)
                if m:
                    title = m.group(1).strip()
                    url = m.group(2).strip()
                    result.append(CITE_WEB_TMPL.format(title=title) + f' - <a href="{url}">{url}</a>')
                    continue
            # Keep non-matching lines as-is
            result.append(line)
        else:
            result.append(line)

    return "\n".join(result)


def scan_all(check_only: bool = False) -> int:
    files = sorted(CONTENT.glob("*.md"))
    formatted = 0

    for f in files:
        text = f.read_text()
        if "### 参考资料" not in text:
            continue
        new_text = format_references(text)
        if new_text != text:
            formatted += 1
            if not check_only:
                f.write_text(new_text)
                print(f"  Formatted: {f.name}")

    print(f"\nFormatted: {formatted} files{' (check only)' if check_only else ''}")
    return formatted


if __name__ == "__main__":
    check_only = "--check" in sys.argv
    single = None
    for i, arg in enumerate(sys.argv):
        if arg == "--file" and i + 1 < len(sys.argv):
            single = Path(sys.argv[i + 1])

    if single:
        if not single.exists():
            print(f"❌ File not found: {single}")
            sys.exit(1)
        text = single.read_text()
        new_text = format_references(text)
        if new_text != text:
            print(f"✅ {single.name}: would reformat")
        else:
            print(f"{single.name}: no changes")
    else:
        scan_all(check_only=check_only)
