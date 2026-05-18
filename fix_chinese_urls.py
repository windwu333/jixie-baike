#!/usr/bin/env python3
"""
修复参见章节中Markdown链接的URL编码问题。
将包含中文等非ASCII字符的URL进行URL编码，确保Markdown渲染后链接可用。

仅处理内部链接（以 / 开头），不处理外部链接。

Usage: python3 fix_chinese_urls.py [--dry-run]
"""

import os
import re
import sys
from urllib.parse import quote

# 项目路径
PROJECT_DIR = "/Users/windwu/Desktop/机械师大百科项目"
CONTENT_DIR = os.path.join(PROJECT_DIR, "content", "website")

# 统计
stats = {
    "files_scanned": 0,
    "files_with_chinese_links": 0,
    "files_modified": 0,
    "links_fixed": 0,
    "errors": 0,
}


def has_non_ascii_in_url(url: str) -> bool:
    """检查URL是否包含需要编码的字符（非ASCII）"""
    for ch in url:
        if ord(ch) > 127:
            return True
    return False


def url_encode_chinese(url: str) -> str:
    """
    URL编码非ASCII字符，保留安全的ASCII字符不变。
    保留 / - _ . ~ : @ ! $ & ' ( ) * + , ; = 等安全字符。
    空格编码为 %20。
    """
    result = []
    i = 0
    while i < len(url):
        ch = url[i]
        # 跳过已有的百分号编码序列
        if ch == '%' and i + 2 < len(url):
            if re.match(r'^[0-9a-fA-F]{2}$', url[i+1:i+3]):
                result.append(url[i:i+3])
                i += 3
                continue
        
        # 安全ASCII字符 - 直接保留
        if ('A' <= ch <= 'Z') or ('a' <= ch <= 'z') or ('0' <= ch <= '9'):
            result.append(ch)
            i += 1
            continue
        
        if ch in "-_.~/:@!$&'()*+,;=":
            result.append(ch)
            i += 1
            continue
        
        # 空格 - 编码为 %20
        if ch == ' ':
            result.append('%20')
            i += 1
            continue
        
        # 非ASCII字符 - URL编码
        if ord(ch) > 127:
            # 用utf-8编码每个字符
            encoded = quote(ch, safe='')
            result.append(encoded)
            i += 1
            continue
        
        # 其他ASCII字符
        result.append(ch)
        i += 1
    
    return ''.join(result)


def fix_links_in_markdown(content: str, filepath: str) -> tuple:
    """
    修复Markdown内容中的中文URL。
    找到 [text](url) 模式的链接，对URL中的中文进行编码。
    
    返回: (修改后的内容, 是否修改, 修改链接数)
    """
    # 匹配Markdown链接: [text](url)
    link_pattern = re.compile(r'(\[.*?\])\(([^)]*)\)')
    
    modified = False
    links_fixed_count = 0
    
    def replace_link(match):
        nonlocal modified, links_fixed_count
        text_part = match.group(1)  # [text]
        url_part = match.group(2)    # url
        
        # 只处理内部链接（以 / 开头）
        if not url_part.startswith('/'):
            return match.group(0)
        
        # 只处理包含非ASCII字符的URL
        if not has_non_ascii_in_url(url_part):
            return match.group(0)
        
        # URL编码非ASCII字符
        new_url = url_encode_chinese(url_part)
        
        if new_url != url_part:
            modified = True
            links_fixed_count += 1
            return f"{text_part}({new_url})"
        
        return match.group(0)
    
    new_content = link_pattern.sub(replace_link, content)
    return new_content, modified, links_fixed_count


def main():
    dry_run = '--dry-run' in sys.argv
    
    if dry_run:
        print("DRY RUN MODE - 不会修改任何文件\n")
    else:
        print("开始修复URL编码问题...\n")
    
    # 扫描所有Markdown文件
    for root, dirs, files in os.walk(CONTENT_DIR):
        for filename in sorted(files):
            if not filename.endswith('.md'):
                continue
            
            filepath = os.path.join(root, filename)
            stats["files_scanned"] += 1
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 快速检查是否包含非ASCII字符在URL中
                # 查找任何 ( 后跟 / 和包含非ASCII字符的URL
                quick_check = re.search(r'\(/[^)]*', content)
                if quick_check:
                    url_candidate = quick_check.group(0)
                    if not has_non_ascii_in_url(url_candidate):
                        continue
                else:
                    continue
                
                # 修复链接
                new_content, was_modified, fix_count = fix_links_in_markdown(content, filepath)
                
                if was_modified:
                    stats["files_with_chinese_links"] += 1
                    stats["links_fixed"] += fix_count
                    
                    rel_path = os.path.relpath(filepath, PROJECT_DIR)
                    print(f"  {rel_path} ({fix_count} links)")
                    
                    if not dry_run:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        stats["files_modified"] += 1
                    
            except Exception as e:
                stats["errors"] += 1
                print(f"  ERROR processing {filepath}: {e}", file=sys.stderr)
    
    # 输出统计
    print(f"\n{'='*50}")
    print(f"统计报告:")
    print(f"  扫描文件数:    {stats['files_scanned']}")
    print(f"  含中文URL文件: {stats['files_with_chinese_links']}")
    print(f"  修改文件数:    {stats['files_modified']}")
    print(f"  修复链接数:    {stats['links_fixed']}")
    print(f"  错误数:        {stats['errors']}")
    
    if dry_run:
        print(f"\n运行时不带 --dry-run 以实际执行修改")


if __name__ == "__main__":
    main()
