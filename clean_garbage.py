#!/usr/bin/env python3
"""
M3-P1-1: 清理垃圾文本（模板残留、英文乱码术语、广告残留）
===========================================================
清理 content/website/ 下MD文件中的：
1. {name} 模板残留语法
2. 英文招聘/广告残留 (FREE Publications, Negotiate Your Salary, Mechanical Engineers Outlook)
3. 英文乱码术语（中英文混杂的无意义术语）
4. 中英混杂的 see-also 链接垃圾
"""

import os
import re
import glob

WEBSITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "website")
MD_FILES = sorted(glob.glob(os.path.join(WEBSITE_DIR, "*.md")))

print(f"目录: {WEBSITE_DIR}")
print(f"找到 {len(MD_FILES)} 个Markdown文件")

# ========================
# 统计计数器
# ========================
stats = {
    "files_modified": set(),
    "name_template": 0,
    "ads_free_salary": 0,
    "ads_me_outlook": 0,
    "mixed_term_related": 0,
    "mixed_term_notes": 0,
    "see_also_broken": 0,
    "broken_source_note": 0,
}

def clean_file(filepath):
    """清理单个文件中的垃圾文本"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    lines = content.split('\n')
    modified_lines = list(lines)
    file_modified = False

    # ============================================================
    # Pattern 1: 清理 {name} 模板残留
    # ============================================================
    new_lines = []
    for line in modified_lines:
        if '{name}' in line:
            # 修复 "## {name}主要内容" -> "## 主要内容"
            line = line.replace('{name}', '')
            # 同时处理 "## 主要内容" 可能变成 "## 主要内容"
            line = re.sub(r'#+\s*主要内容', '## 主要内容', line)
            stats["name_template"] += 1
            file_modified = True
        new_lines.append(line)
    modified_lines = new_lines

    # ============================================================
    # Pattern 2: 清理术语注释区块中的广告残留
    # ============================================================
    new_lines = []
    for line in modified_lines:
        original_line = line
        
        # 2a: "FREE Publications Negotiate Your Salary Learn the best principles to negotiate the salary you deserve!"
        if 'Negotiate Your Salary' in line:
            line = re.sub(
                r'—\s*FREE Publications\s+Negotiate Your Salary\s+Learn the best principles to negotiate the salary you deserve!',
                '—',
                line
            )
            stats["ads_free_salary"] += 1
            file_modified = True
        
        # 2a-2: "Negotiate Your Salary" standalone (without FREE Publications prefix)
        if 'Negotiate Your Salary' in line:
            line = re.sub(
                r'—\s*Negotiate Your Salary\s+Learn the best principles to negotiate the salary you deserve!',
                '—',
                line
            )
            stats["ads_free_salary"] += 1
            file_modified = True
        
        # 2b: "Mechanical Engineers Outlook Guide for those interested in becoming a mechanical engineer."
        if 'Mechanical Engineers Outlook' in line:
            line = re.sub(
                r'—\s*Mechanical Engineers Outlook Guide for those interested in becoming a mechanical engineer\.',
                '—',
                line
            )
            stats["ads_me_outlook"] += 1
            file_modified = True
        
        # 2c: Clean "designing塑料parts" type garbage in term entries
        # Pattern: **designing塑料parts** (Designing Plastic Parts) — Mechanical Engineers Outlook...
        if 'designing塑料parts' in line or 'Designing Plastic Parts' in line:
            # Remove entire entry if it's just ad garbage
            if 'Mechanical Engineers Outlook' in line or ('Designing Plastic Parts' in line and line.strip().startswith('[^t')):
                line = re.sub(
                    r'\[\^t\d+\]:\s*\*\*designing塑料parts\*\*\s*\(Designing Plastic Parts\).*',
                    '',
                    line
                )
                file_modified = True
        
        if original_line != line:
            file_modified = True
        new_lines.append(line)
    modified_lines = new_lines

    # ============================================================
    # Pattern 3: 清理中英混杂的乱码术语（在"相关专业术语"行中）
    # ============================================================
    new_lines = []
    for line in modified_lines:
        original_line = line
        
        # 只在包含"相关专业术语"的行中进行清理
        if '相关专业术语' in line:
            # 替换已知的垃圾混合术语
            replacements = [
                # 完全垃圾术语 → 移除
                (r'精度sprocketscaliperdiametersperansiasmebm\[\^t\d+\]', ''),
                (r'精度sprocketscaliper\[\^t\d+\]', ''),
                (r'reference滚子链条\[\^t\d+\]', ''),
                (r'滚子链条no\[\^t\d+\]', ''),
                (r'滚子链条nohorsepowerand速度ratings\[\^t\d+\]', ''),
                (r'滚子链条链轮diametersdimesionsperansiasmebm\[\^t\d+\]', ''),
                (r'servicefactors滚子链条驱动工作台\[\^t\d+\]', ''),
                (r'designing塑料parts\[\^t\d+\]', ''),
                (r'asmeansigdtwriterand发电机\[\^t\d+\]', ''),
            ]
            
            for pattern, replacement in replacements:
                if re.search(pattern, line):
                    line = re.sub(pattern, replacement, line)
                    stats["mixed_term_related"] += 1
                    file_modified = True
            
            # 清理残留的逗号和空格（移除多余的逗号）
            line = re.sub(r',\s*,', ',', line)
            line = re.sub(r',\s*$', '', line)
            line = line.rstrip('、，, ')
        
        if original_line != line:
            file_modified = True
        new_lines.append(line)
    modified_lines = new_lines

    # ============================================================
    # Pattern 4: 清理中英混杂的乱码术语注释条目
    # ============================================================
    new_lines = []
    for line in modified_lines:
        original_line = line
        
        # 匹配术语注释行 [^tN]: **garbage** (...)
        # 移除整条注释如果术语名包含中英混杂垃圾
        garbage_term_patterns = [
            r'\[\^t\d+\]:\s*\*\*精度sprocketscaliper\*\*.*',
            r'\[\^t\d+\]:\s*\*\*精度sprocketscaliperdiametersperansiasmebm\*\*.*',
            r'\[\^t\d+\]:\s*\*\*滚子链条no\*\*.*',
            r'\[\^t\d+\]:\s*\*\*滚子链条nohorsepowerand速度ratings\*\*.*',
            r'\[\^t\d+\]:\s*\*\*滚子链条链轮diametersdimesionsperansiasmebm\*\*.*',
            r'\[\^t\d+\]:\s*\*\*servicefactors滚子链条驱动工作台\*\*.*',
            r'\[\^t\d+\]:\s*\*\*designing塑料parts\*\*.*',
        ]
        
        for pattern in garbage_term_patterns:
            if re.match(pattern, line):
                line = ''
                stats["mixed_term_notes"] += 1
                file_modified = True
                break
        
        if original_line != line:
            file_modified = True
        new_lines.append(line)
    modified_lines = new_lines

    # ============================================================
    # Pattern 5: 清理 broken "来源:" lines that followed deleted term notes
    # 删除空行后的 "来源: subterm_extraction" 或 "来源: efunda" 如果是孤立无注释的
    # ============================================================
    new_lines = []
    skip_next = False
    for i, line in enumerate(modified_lines):
        if skip_next:
            skip_next = False
            # 检查是否为 "来源:" 行
            if line.strip().startswith('来源:'):
                stats["broken_source_note"] += 1
                file_modified = True
                continue
            else:
                new_lines.append(line)
                continue
        new_lines.append(line)
        # 如果当前行是空行且上一行（已添加的最后一个）也是空行，标记下一个
        # Actually, let me handle this differently - after removing a term note line,
        # the following "来源:" line should also be removed if it exists
        pass
    
    # Better approach: remove orphaned "来源:" lines
    # Lines that are just "      来源: efunda" or "      来源: subterm_extraction" 
    # but NOT preceded by a valid term note
    cleaned = []
    i = 0
    while i < len(modified_lines):
        line = modified_lines[i]
        stripped = line.strip()
        
        # Check if this is a "来源:" line preceded by an empty line or another "来源:" line
        if stripped.startswith('来源:'):
            # Look back to see if there's a valid term note before it
            # (ignoring blank lines)
            prev_content = None
            for j in range(i-1, -1, -1):
                prev_stripped = modified_lines[j].strip()
                if prev_stripped:
                    prev_content = prev_stripped
                    break
            
            if prev_content and (prev_content.startswith('[^t') or prev_content.startswith('来源:')):
                # Valid - keep it
                cleaned.append(line)
            else:
                # Orphaned - remove it
                stats["broken_source_note"] += 1
                file_modified = True
        else:
            cleaned.append(line)
        i += 1
    modified_lines = cleaned

    # ============================================================
    # Pattern 6: 清理参见链接中的乱码
    # ============================================================
    new_lines = []
    for line in modified_lines:
        original_line = line
        
        # 清理 see-also 链接中的垃圾
        broken_see_also = [
            (r'- \[asmeansigdtwriterand发电机\].*', ''),
            (r'- \[精度sprocketscaliperdiametersperansiasmebm\].*', ''),
            (r'- \[精度sprocketscaliper\].*', ''),
        ]
        
        for pattern, replacement in broken_see_also:
            if re.match(pattern, line):
                line = replacement
                stats["see_also_broken"] += 1
                file_modified = True
                break
        
        if original_line != line:
            file_modified = True
        new_lines.append(line)
    modified_lines = new_lines

    # ============================================================
    # Pattern 7: 清理多余的连续空行（超过2个）
    # ============================================================
    cleaned_lines = []
    empty_count = 0
    for line in modified_lines:
        if line.strip() == '':
            empty_count += 1
            if empty_count <= 2:
                cleaned_lines.append(line)
        else:
            empty_count = 0
            cleaned_lines.append(line)
    modified_lines = cleaned_lines

    # ============================================================
    # 写回文件
    # ============================================================
    new_content = '\n'.join(modified_lines)
    
    if new_content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        stats["files_modified"].add(filepath)
        return True
    else:
        return file_modified  # fallback check


# ========================
# 执行清理
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
# 统计报告
# ========================
print("\n" + "=" * 60)
print("清理统计报告")
print("=" * 60)
print(f"总共扫描文件:       {len(MD_FILES)}")
print(f"实际修改文件:       {total_modified}")
print(f"  - {stats['name_template']} 处 '{{name}}' 模板残留")
print(f"  - {stats['ads_free_salary']} 处 FREE Publications 广告")
print(f"  - {stats['ads_me_outlook']} 处 Mechanical Engineers Outlook 广告") 
print(f"  - {stats['mixed_term_related']} 处 相关专业术语中的乱码")
print(f"  - {stats['mixed_term_notes']} 处 术语注释中的乱码条目")
print(f"  - {stats['see_also_broken']} 处 参见链接中的乱码")
print(f"  - {stats['broken_source_note']} 处 孤立来源行")
print("=" * 60)
