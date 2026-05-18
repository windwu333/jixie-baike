#!/usr/bin/env python3
"""Phase E4-v2: Final cleanup - classify remaining untranslated terms and finalize v8

Usage: python3 scripts/phase-e4-v2-finalize.py
"""
import json, re
from pathlib import Path
from datetime import date

BASE = Path(__file__).parent.parent
KB = BASE / "knowledge-base"

def load_json(path):
    return json.loads(path.read_bytes()) if path.exists() else None

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

def has_chinese(s):
    return bool(re.search(r'[一-鿿]', s))

# Known Chinese acronyms that should remain in English
ACRONYMS = {
    "3d", "cad", "cam", "cae", "capp", "pdm", "plm", "erp", "mrp", "cims",
    "cnc", "nc", "dnc", "fms", "cmm", "plc", "pid", "hmi", "scada", "dcs",
    "led", "lcd", "ccd", "abs", "esp", "iso", "gb", "ansi", "din", "jis",
    "pwm", "vfd", "ac", "dc", "rpm", "hp", "kw", "hz",
    "mig", "tig", "mag", "ndt", "fmea", "spc", "api", "asme", "astm", "sae",
    "iec", "vdi", "aisc", "bs", "en", "gost", "iso", "ansi",
}

def classify_term(en, zh):
    """Classify a term by translation status and type"""
    if not zh:
        return "empty", "missing_translation"

    if not has_chinese(zh) and not re.search(r'[a-zA-Z]', zh):
        return "empty", "no_content"

    # Pure English (no Chinese characters)
    if not has_chinese(zh):
        en_lower = en.strip().lower()
        zh_lower = zh.strip().lower()

        # Check if unchanged
        if zh_lower == en_lower or zh_lower == en_lower.replace("'", ""):
            return "untranslated", "exact_copy"

        # Check if it's an acronym
        words = en.strip().split()
        all_acronym = all(w.isupper() and len(w) <= 5 for w in words if w.isalpha())
        if all_acronym and len(words) >= 1:
            return "untranslated", "acronym"

        # Check if it's a person name
        person_pattern = re.compile(
            r'^[A-Z][a-zéèêëàâäùûüôöîï]+(\s+[A-Z][a-zéèêëàâäùûüôöîï.]+){1,4}$'
        )
        if person_pattern.match(en):
            return "untranslated", "person_name"

        # Check if it's an organization
        org_words = ['University', 'Institute', 'College', 'School', 'Association',
                     'Society', 'Laboratory', 'Centre', 'Center', 'Foundation',
                     'Council', 'Commission', 'Committee', 'Organization', 'Company',
                     'Inc', 'Ltd', 'Corporation', 'International', 'Standard',
                     'Engineers', 'Handbook', 'Manual', 'Guide', 'Journal',
                     'Proceedings', 'Transactions', 'Review', 'Report']
        if any(w in en.split() for w in org_words):
            return "untranslated", "organization"

        # Check if it's a named standard/spec
        if re.search(r'\b(BS|EN|ISO|ASTM|AISI|DIN|JIS|GB|SAE)\s', en):
            return "untranslated", "standard"

        # Look for single technical terms that have standard translations
        simple_term = len(en.split()) == 1 and not en[0].isupper()
        if simple_term:
            return "untranslated", "single_term"

        # Multi-word generic
        if en[0].islower():
            return "untranslated", "generic_multi"

        # Default
        if len(en.split()) >= 3:
            return "untranslated", "long_name"
        return "untranslated", "proper_noun"

    # Has Chinese + English (mixed)
    lower_en_words = re.findall(r'[a-z]+', zh)
    if lower_en_words:
        # Check if the mixed zh is just a partial translation
        if len(lower_en_words) <= 3:
            return "partial", "minor_mix"
        else:
            return "partial", "heavy_mix"

    return "verified", "verified"


def main():
    print("=" * 60)
    print("Phase E4-v2: 术语翻译最终分类")
    print(f"日期: {date.today().isoformat()}")
    print("=" * 60)

    # Load v7
    v7 = load_json(KB / "mech-terminology-v7.json")
    if not v7:
        # Try v6
        v7 = load_json(KB / "mech-terminology-v6.json")
    if not v7:
        print("ERROR: Cannot find terminology file")
        return

    terms = v7.get("terms", [])
    print(f"\n加载: {len(terms)} terms")

    # Classify all terms
    categories = {}
    for t in terms:
        en = t.get("en", "")
        zh = t.get("zh", "")
        status, subtype = classify_term(en, zh)
        key = f"{status}:{subtype}"
        categories.setdefault(key, []).append(t)
        t["translation_status"] = status
        t["translation_subtype"] = subtype

    # Print summary
    print(f"\n{'='*60}")
    print(f"翻译状态分布")
    print(f"{'='*60}")
    verified_count = 0
    for key in sorted(categories.keys()):
        count = len(categories[key])
        is_verified = key.startswith("verified")
        if is_verified:
            verified_count += count
        icon = "✓" if is_verified else "✗"
        print(f"  {icon} {key:40s}: {count:4d}")

    # Detailed breakdown of untranslated
    untranslated_types = {k: v for k, v in categories.items() if k.startswith("untranslated")}
    if untranslated_types:
        print(f"\n{'='*60}")
        print(f"未翻译术语分类")
        print(f"{'='*60}")
        for key in sorted(untranslated_types.keys()):
            terms_list = untranslated_types[key][:5]
            print(f"\n  {key} ({len(untranslated_types[key])}):")
            for t in terms_list:
                print(f"    {t['en'][:60]:60s} source: {t.get('source', '?')}")
            if len(untranslated_types[key]) > 5:
                print(f"    ... 还有 {len(untranslated_types[key])-5} 条")

    # Save v8
    v7["meta"]["version"] = "8"
    v7["meta"]["version_date"] = date.today().isoformat()
    v7["meta"]["verified_count"] = verified_count
    v7["meta"]["untranslated_count"] = sum(len(v) for k, v in categories.items() if k.startswith("untranslated"))
    v7["meta"]["partial_count"] = sum(len(v) for k, v in categories.items() if k.startswith("partial"))

    v8_path = KB / "mech-terminology-v8.json"
    save_json(v8_path, v7)
    print(f"\n✅ 已保存 v8: {v8_path}")

    # Generate issue list
    generate_issue_list(categories)

    return v7


def generate_issue_list(categories):
    """Generate a clean issue report for remaining problem terms"""
    output = []
    output.append("# 术语翻译待处理清单\n")
    output.append(f"生成日期: {date.today().isoformat()}\n")
    output.append("## 总览\n")
    output.append("| 分类 | 数量 | 说明 |")
    output.append("|------|------|------|")

    total = 0
    for key in sorted(categories.keys()):
        count = len(categories[key])
        if not key.startswith("verified"):
            status, subtype = key.split(":", 1)
            desc = {
                "partial:minor_mix": "中英混合（少量英文遗留）",
                "partial:heavy_mix": "中英混合（大量英文遗留）",
                "untranslated:exact_copy": "完全未翻译（zh==en）",
                "untranslated:acronym": "纯英文缩写",
                "untranslated:person_name": "人名（无需翻译）",
                "untranslated:organization": "机构/组织名（需保持英文）",
                "untranslated:standard": "标准代号（需保持英文）",
                "untranslated:single_term": "单英文词汇（需专业翻译）",
                "untranslated:generic_multi": "多词组合（可翻译）",
                "untranslated:long_name": "长名称/标题（需评估）",
                "untranslated:proper_noun": "专有名词（需保持英文）",
                "empty:missing_translation": "缺失翻译",
                "empty:no_content": "无内容",
            }.get(key, key)
            output.append(f"| {key} | {count} | {desc} |")
            total += count

    output.append(f"\n**待处理总计: {total} 条**\n")

    # Detailed lists
    for key in sorted(categories.keys()):
        if not key.startswith("verified"):
            terms_list = categories[key]
            output.append(f"\n## {key} ({len(terms_list)} 条)\n")
            output.append("| 英文 | 当前中文 | 来源 | 分类 |")
            output.append("|------|---------|------|------|")
            for t in terms_list[:50]:
                output.append(f"| {t['en'][:60]} | {t.get('zh', '')[:40]} | {t.get('source', '')[:20]} | {t.get('category', '')[:20]} |")
            if len(terms_list) > 50:
                output.append(f"| ... 还有 {len(terms_list)-50} 条 | | | |")

    issue_path = KB / "terminology-issue-list-v2.md"
    save_json(issue_path, output)  # Hmm, wrong function
    issue_path.write_text("\n".join(output), encoding="utf-8")
    print(f"📋 问题清单: {issue_path}")


if __name__ == "__main__":
    main()
