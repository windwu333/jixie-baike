#!/usr/bin/env python3
"""
Script to find all Markdown files with English or mixed Chinese-English titles.
"""
import os
import re
import yaml

CONTENT_DIR = "/Users/windwu/Desktop/机械师大百科项目/content/website"

def has_chinese(text):
    """Check if text contains Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]', text))

def is_pure_english(text):
    """Check if text is pure English (no Chinese characters)."""
    return not has_chinese(text) and bool(re.search(r'[a-zA-Z]', text))

def is_mixed(text):
    """Check if text has both Chinese and English."""
    return has_chinese(text) and bool(re.search(r'[a-zA-Z]', text))

def extract_title(filepath):
    """Extract the title from frontmatter."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Match YAML frontmatter
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None
    
    yaml_block = match.group(1)
    try:
        data = yaml.safe_load(yaml_block)
        if data and 'title' in data:
            return data['title']
    except:
        pass
    
    # Fallback: manual regex
    title_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', yaml_block, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip().strip('"').strip("'")
    
    return None

results = {
    'pure_english': [],
    'mixed': [],
    'error': []
}

for root, dirs, files in os.walk(CONTENT_DIR):
    for fname in files:
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(root, fname)
        
        title = extract_title(fpath)
        if title is None:
            results['error'].append((fpath, 'No title'))
            continue
        
        rel_path = os.path.relpath(fpath, CONTENT_DIR)
        
        if is_pure_english(title):
            results['pure_english'].append((rel_path, title))
        elif is_mixed(title):
            results['mixed'].append((rel_path, title))

print(f"=== 统计结果 ===")
print(f"纯英文标题: {len(results['pure_english'])} 篇")
print(f"中英混杂标题: {len(results['mixed'])} 篇")
print(f"需要翻译总数: {len(results['pure_english']) + len(results['mixed'])} 篇")
print(f"无法读取标题: {len(results['error'])} 篇")
print()

if results['pure_english']:
    print(f"=== 纯英文标题前30个 ===")
    for path, title in results['pure_english'][:30]:
        print(f"  {path} -> '{title}'")

if results['mixed']:
    print(f"\n=== 中英混杂标题前30个 ===")
    for path, title in results['mixed'][:30]:
        print(f"  {path} -> '{title}'")

# Save full results to file
output_path = "/Users/windwu/Desktop/机械师大百科项目/english_titles_report.txt"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(f"纯英文标题: {len(results['pure_english'])} 篇\n")
    f.write(f"中英混杂标题: {len(results['mixed'])} 篇\n")
    f.write(f"需要翻译总数: {len(results['pure_english']) + len(results['mixed'])} 篇\n\n")
    
    f.write("=== 纯英文标题 ===\n")
    for path, title in results['pure_english']:
        f.write(f"{path}\t{title}\n")
    
    f.write("\n=== 中英混杂标题 ===\n")
    for path, title in results['mixed']:
        f.write(f"{path}\t{title}\n")

print(f"\n完整报告已保存到: {output_path}")
