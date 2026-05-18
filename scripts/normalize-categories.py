#!/usr/bin/env python3
"""Normalize overlapping category names in mech-terminology-v3.json"""
import json
from collections import Counter

CAT_NORMALIZE = {
    '热工流体': '热工与流体',
    '力学强度': '力学与强度分析',
    '机电自动化': '机械电子与自动化',
    '制图CAD': '机械制图与CAD',
    '标准规范': '标准与规范',
}

path = '/Users/windwu/Desktop/机械师大百科项目/knowledge-base/mech-terminology-v3.json'
t = json.load(open(path))

fixed = 0
for entry in t['terms'] + t['extracted_extras']:
    old_cat = entry.get('category', '')
    if old_cat in CAT_NORMALIZE:
        entry['category'] = CAT_NORMALIZE[old_cat]
        fixed += 1

cats = Counter(entry.get('category', '?') for entry in t['terms'] + t['extracted_extras'])
t['meta']['category_distribution'] = dict(cats.most_common())
t['meta']['category_normalized'] = True

json.dump(t, open(path, 'w'), ensure_ascii=False, indent=2)
print(f'Normalized {fixed} categories')
for c, n in cats.most_common():
    print(f'  {c}: {n}')
