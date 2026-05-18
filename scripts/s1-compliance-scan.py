#!/usr/bin/env python3
"""
S1 Compliance Scan — 机械师大百科

S1 标准: 每篇文章必须有术语注释 ([^tN] 脚注) 和来源引用。
扫描 content/website/*.md, 输出 JSON 合规报告.
"""

import glob
import json
import os
import re
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(PROJECT_ROOT, "content", "website")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "content", "s1-compliance-report.json")

# 中文字符正则
RE_CHINESE = re.compile(r"[一-鿿]")

# 脚注引用: [^t数字] 或 [^t数字-字母]
RE_FOOTNOTE_REF = re.compile(r"\[\^t[\d-]+\]")

# 脚注定义: [^t数字]: ...
RE_FOOTNOTE_DEF = re.compile(r"^\[\^t[\d-]+\]:")

# 来源行
RE_SOURCE_LINE = re.compile(r"来源\s*:")


def extract_article_id(filename: str) -> str:
    """从文件名提取文章 ID (去掉 .md 和日期前缀)."""
    base = os.path.splitext(os.path.basename(filename))[0]
    return base


def read_file(path: str) -> str | None:
    """安全读取文件, 返回内容或 None."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def split_sections(text: str) -> tuple[str, str, str]:
    """将文章拆分为: frontmatter, body, footnotes.

    返回: (frontmatter, body, footnotes_section)
    - frontmatter: YAML 头部 (不含 ---)
    - body: 正文 (第一个 --- 之后, 第二个 --- 之前)
    - footnotes_section: 第二个 --- 之后的内容 (术语注释段落)
    """
    # 去掉 frontmatter
    parts = text.split("---", 2)
    if len(parts) < 3:
        return ("", text, "")

    frontmatter = parts[1].strip()
    rest = parts[2]

    # 找正文和脚注的分隔 (第二个 ---)
    sep_idx = rest.find("\n---\n")
    if sep_idx == -1:
        # 可能文件以 --- 结尾?
        sep_idx = rest.find("\n---")
        if sep_idx == -1:
            return (frontmatter, rest.strip(), "")

    body = rest[:sep_idx].strip()
    footnotes_section = rest[sep_idx + 4:].strip()
    return (frontmatter, body, footnotes_section)


def count_chinese(text: str) -> int:
    """统计中文字符数."""
    return len(RE_CHINESE.findall(text))


def check_footnotes_defined(footnotes_section: str, refs: list[str]) -> tuple[list[str], list[str]]:
    """检查脚注引用是否有对应定义.

    返回: (defined_refs, undefined_refs)
    """
    defined = set()
    for line in footnotes_section.split("\n"):
        if RE_FOOTNOTE_DEF.match(line):
            m = re.match(r"\[\^(t[\d-]+)\]", line)
            if m:
                defined.add(m.group(1))

    defined_refs = []
    undefined_refs = []
    for ref in refs:
        m = re.match(r"\[\^(t[\d-]+)\]", ref)
        if m:
            key = m.group(1)
            if key in defined:
                defined_refs.append(ref)
            else:
                undefined_refs.append(ref)
    return (defined_refs, undefined_refs)


def check_sources(footnotes_section: str) -> tuple[int, int]:
    """检查脚注定义段中有多少定义包含来源引用.

    返回: (with_source, total_defs)
    处理多行脚注: 定义行后的缩进延续行中查找 来源:
    """
    lines = footnotes_section.split("\n")
    total_defs = 0
    with_source = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        if RE_FOOTNOTE_DEF.match(line):
            total_defs += 1
            # 检查本行是否包含来源
            if RE_SOURCE_LINE.search(line):
                with_source += 1
            else:
                # 检查后续缩进行
                j = i + 1
                while j < len(lines) and (lines[j].startswith((" ", "\t")) or not lines[j].strip()):
                    if RE_SOURCE_LINE.search(lines[j]):
                        with_source += 1
                        break
                    j += 1
        i += 1

    return (with_source, total_defs)


def scan_article(path: str) -> dict:
    """扫描单篇文章, 返回合规检查结果."""
    result = {
        "file": os.path.basename(path),
        "article_id": extract_article_id(path),
        "compliant": False,
        "failures": [],
    }

    text = read_file(path)
    if text is None:
        result["failures"].append("file_read_error")
        return result

    frontmatter, body, footnotes_section = split_sections(text)

    # 1. 中文字数 > 200
    chinese_count = count_chinese(frontmatter + body)
    if chinese_count <= 200:
        result["failures"].append(f"chinese_chars_{chinese_count}_le_200")
    result["chinese_chars"] = chinese_count

    # 2. 是否有 [^t 脚注引用
    refs = RE_FOOTNOTE_REF.findall(body)
    if not refs:
        result["failures"].append("no_footnote_refs")
    else:
        result["footnote_refs"] = len(refs)

    # 3. 是否有脚注定义段落
    if not footnotes_section:
        result["failures"].append("no_footnote_section")
    else:
        # 4. 定义行数量
        def_lines = [l for l in footnotes_section.split("\n") if RE_FOOTNOTE_DEF.match(l)]
        result["footnote_defs"] = len(def_lines)
        if not def_lines:
            result["failures"].append("no_footnote_defs")

        # 5. 来源引用
        with_src, total_defs = check_sources(footnotes_section)
        result["sources_found"] = with_src
        if with_src == 0 and total_defs > 0:
            result["failures"].append("no_source_citations")

        # 6. 检查脚注引用有定义
        if refs:
            defined_refs, undefined_refs = check_footnotes_defined(footnotes_section, refs)
            if undefined_refs:
                result["failures"].append(f"undefined_footnotes_{len(undefined_refs)}")
            result["defined_refs"] = len(defined_refs)
            result["undefined_refs"] = len(undefined_refs)

    # 综合判断: 无任何失败则合规
    result["compliant"] = len(result["failures"]) == 0
    return result


def main():
    if not os.path.isdir(CONTENT_DIR):
        print(f"Error: content directory not found: {CONTENT_DIR}", file=sys.stderr)
        sys.exit(1)

    files = sorted(glob.glob(os.path.join(CONTENT_DIR, "*.md")))
    if not files:
        print(f"Error: no markdown files found in {CONTENT_DIR}", file=sys.stderr)
        sys.exit(1)

    total = len(files)
    results = []
    failed = []
    failure_reasons = {}

    for path in files:
        r = scan_article(path)
        results.append(r)
        if not r["compliant"]:
            aid = r["article_id"]
            failed.append(aid)
            for f in r["failures"]:
                failure_reasons.setdefault(f, [])
                failure_reasons[f].append(aid)

    compliant_count = sum(1 for r in results if r["compliant"])
    rate = round(compliant_count / total, 4)
    pass_flag = rate >= 0.80

    report = {
        "total": total,
        "compliant": compliant_count,
        "failed": failed,
        "failure_reasons": failure_reasons,
        "compliance_rate": rate,
        "pass": pass_flag,
    }

    # 输出到文件
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    summary = f"[S1 Scan] {total} files, {compliant_count} compliant, rate={rate:.2%}, pass={pass_flag}"
    print(summary)
    if not pass_flag:
        for reason, ids in sorted(failure_reasons.items()):
            print(f"  FAIL: {reason} ({len(ids)} files)")


if __name__ == "__main__":
    main()
