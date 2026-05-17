#!/usr/bin/env python3
"""Hugo Markdown → 微信公众号文章格式转换器"""
import re, sys
from pathlib import Path

WECHAT_DISCLAIMER = (
    "\n---\n"
    "📌 这是机械师大百科系列内容，欢迎关注获取更多机械工程知识。\n"
)

def strip_frontmatter(text: str) -> str:
    """Remove Hugo YAML/TOML frontmatter."""
    if text.startswith("---"):
        _, *rest = text.split("---", 2)
        return rest[1] if len(rest) > 1 else rest[0]
    return text

def convert_heading(line: str) -> str:
    """Convert ## heading → ▎heading (WeChat style)."""
    m = re.match(r"^(#{1,3})\s+(.+)$", line)
    if m:
        return f"▎{m.group(2).strip()}\n"
    return line

def convert_bold(line: str) -> str:
    """Keep **bold** as-is (WeChat supports it)."""
    return line

def add_separators(text: str) -> str:
    """Add decorative separators between major sections."""
    lines = text.split("\n")
    result = []
    for line in lines:
        if line.startswith("▎"):
            if result:
                result.append("")
            result.append(line)
        else:
            result.append(line)
    return "\n".join(result)

def hugo2wechat(input_path: str, output_path: str | None = None) -> str:
    """Convert Hugo MD to WeChat-compatible format."""
    content = Path(input_path).read_text()

    # Strip YAML frontmatter
    body = strip_frontmatter(content).strip()

    # Convert headings
    lines = body.split("\n")
    converted = []
    for line in lines:
        line = convert_heading(line)
        converted.append(line)

    result = "\n".join(converted).strip()

    # Add disclaimer
    result += WECHAT_DISCLAIMER

    if output_path:
        Path(output_path).write_text(result)
        print(f"✅ {input_path} → {output_path}")

    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: hugo2wechat.py <input.md> [output.md]", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    hugo2wechat(input_path, output_path)

if __name__ == "__main__":
    main()
