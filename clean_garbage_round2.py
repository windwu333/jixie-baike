#!/usr/bin/env python3
"""
M3-P1-1: 清理垃圾文本（第二轮 - 补充清理）
清理以下新增模式：
1. 设计塑料设计 在 相关专业术语/术语注释/参见链接
2. designing塑料parts 在 参见链接
3. cored层压复合材料刚度equationsand 在 各位置
4. reference滚子链条 在 术语注释
5. 弹性复合材料材料 在 相关专业术语/术语注释（非文章主体）
6. 其他混合乱码
"""

import os
import re
import glob

WEBSITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "website")
MD_FILES = sorted(glob.glob(os.path.join(WEBSITE_DIR, "*.md")))

print(f"目录: {WEBSITE_DIR}")
print(f"找到 {len(MD_FILES)} 个Markdown文件")

stats = {
    "files_modified": set(),
    "related_term_cleaned": 0,
    "term_note_cleaned": 0,
    "see_also_cleaned": 0,
    "orphan_source": 0,
}

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    lines = content.split('\n')
    file_modified = False

    # ============================================================
    # 1. 清理参见链接中的垃圾
    # ============================================================
    new_lines = []
    garbage_see_also = [
        r'^- \[设计塑料设计\].*',
        r'^- \[designing塑料parts\].*',
        r'^- \[cored层压复合材料刚度equationsand\].*',
        r'^- \[弹性复合材料材料\].*',
        r'^- \[reference滚子链条\].*',
        r'^- \[滚子链条no\].*',
        r'^- \[滚子链条nohorsepowerand速度ratings\].*',
        r'^- \[滚子链条链轮diametersdimesionsperansiasmebm\].*',
        r'^- \[servicefactors滚子链条驱动工作台\].*',
        r'^- \[精度sprocketscaliper\].*',
        r'^- \[精度sprocketscaliperdiametersperansiasmebm\].*',
        r'^- \[asmeansigdtwriterand发电机\].*',
    ]
    
    for line in modified_lines if False else lines:
        pass  # We'll rebuild below
    
    # Actually, let me just build from the existing lines
    modified_lines = list(lines)
    
    new_lines = []
    for line in modified_lines:
        stripped = line.strip()
        matched = False
        for pattern in garbage_see_also:
            if re.match(pattern, stripped):
                matched = True
                stats["see_also_cleaned"] += 1
                file_modified = True
                break
        if not matched:
            new_lines.append(line)
    modified_lines = new_lines

    # ============================================================
    # 2. 清理"相关专业术语"行中的乱码术语
    # ============================================================
    new_lines = []
    garbage_related_terms = [
        r'设计塑料设计\[\^t\d+\]',
        r'cored层压复合材料刚度equationsand\[\^t\d+\]',
        r'弹性复合材料材料\[\^t\d+\]',
        r'reference滚子链条\[\^t\d+\]',
    ]
    
    for line in modified_lines:
        if '相关专业术语' in line:
            for pattern in garbage_related_terms:
                if re.search(pattern, line):
                    line = re.sub(pattern, '', line)
                    stats["related_term_cleaned"] += 1
                    file_modified = True
            # Clean up extra commas/spaces
            line = re.sub(r',\s*,', ',', line)
            line = re.sub(r',\s*$', '', line)
            line = line.rstrip('、，, ')
        new_lines.append(line)
    modified_lines = new_lines

    # ============================================================
    # 3. 清理术语注释中的乱码条目
    # ============================================================
    new_lines = []
    garbage_term_notes = [
        r'\[\^t\d+\]:\s*\*\*设计塑料设计\*\*.*',
        r'\[\^t\d+\]:\s*\*\*cored层压复合材料刚度equationsand\*\*.*',
        r'\[\^t\d+\]:\s*\*\*弹性复合材料材料\*\*.*',
        r'\[\^t\d+\]:\s*\*\*reference滚子链条\*\*.*',
    ]
    
    for line in modified_lines:
        stripped = line.strip()
        matched = False
        for pattern in garbage_term_notes:
            if re.match(pattern, stripped):
                matched = True
                stats["term_note_cleaned"] += 1
                file_modified = True
                break
        if not matched:
            new_lines.append(line)
    modified_lines = new_lines

    # ============================================================
    # 4. 清理因删除注释条目而孤立的"来源:"行
    # ============================================================
    cleaned = []
    i = 0
    while i < len(modified_lines):
        line = modified_lines[i]
        stripped = line.strip()
        
        if stripped.startswith('来源:'):
            # Look back for a valid preceeding term note
            prev_content = None
            for j in range(i-1, -1, -1):
                prev_stripped = modified_lines[j].strip()
                if prev_stripped:
                    prev_content = prev_stripped
                    break
            
            if prev_content and (prev_content.startswith('[^t') or prev_content.startswith('来源:')):
                cleaned.append(line)
            else:
                # Orphaned source line - remove
                stats["orphan_source"] += 1
                file_modified = True
        else:
            cleaned.append(line)
        i += 1
    modified_lines = cleaned

    # ============================================================
    # 5. 清理多余的连续空行
    # ============================================================
    final_lines = []
    empty_count = 0
    for line in modified_lines:
        if line.strip() == '':
            empty_count += 1
            if empty_count <= 2:
                final_lines.append(line)
        else:
            empty_count = 0
            final_lines.append(line)
    modified_lines = final_lines

    # ============================================================
    # 写回
    # ============================================================
    new_content = '\n'.join(modified_lines)
    if new_content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        stats["files_modified"].add(filepath)
        return True
    
    return file_modified


# ========================
# 执行
# ========================
total_modified = 0
for filepath in MD_FILES:
    try:
        if clean_file(filepath):
            total_modified += 1
            print(f"  ✓ 已修改: {os.path.basename(filepath)}")
    except Exception as e:
        print(f"  ✗ 错误 {os.path.basename(filepath)}: {e}")

# ========================
# 统计
# ========================
print("\n" + "=" * 60)
print("第二轮清理统计报告")
print("=" * 60)
print(f"总共扫描文件:       {len(MD_FILES)}")
print(f"实际修改文件:       {total_modified}")
print(f"  - {stats['see_also_cleaned']} 处 参见链接乱码")
print(f"  - {stats['related_term_cleaned']} 处 相关专业术语乱码")
print(f"  - {stats['term_note_cleaned']} 处 术语注释条目乱码")
print(f"  - {stats['orphan_source']} 处 孤立来源行")
print("=" * 60)
