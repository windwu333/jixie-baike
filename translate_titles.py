#!/usr/bin/env python3
"""
M3-P1-2: 翻译未处理英文标题
方案A: 基于预设词典的规则映射翻译
"""

import os
import re
import json

CONTENT_DIR = "/Users/windwu/Desktop/机械师大百科项目/content/website"
REPORT_FILE = "/Users/windwu/Desktop/机械师大百科项目/title_translation_report.txt"

# ===== 专业术语词典 =====
# 机械工程专用英汉翻译词典
TRANSLATION_DICT = {
    # 标准与规范
    "DIN": "DIN标准",
    "EN": "EN标准",
    "ISO": "ISO标准",
    "iec": "IEC标准",
    "IEC": "IEC标准",
    "CE": "CE认证",
    "ce": "CE认证",
    "bs": "BS标准",
    "gb": "GB标准",
    "GB": "GB标准",
    "SAE": "SAE标准",
    "ANSI": "ANSI标准",
    "ASME": "ASME标准",
    "ASTM": "ASTM标准",
    "nace": "NACE标准",
    "AWS": "AWS标准",
    "ul": "UL标准",
    "api": "API标准",
    "ieee": "IEEE标准",
    "IEEE": "IEEE标准",
    "ATEX": "ATEX防爆认证",
    "GB标准": "GB标准",
    "JB标准": "JB标准",
    "CE认证": "CE认证",
    "ISO标准": "ISO标准",
    "ISO机械安全": "ISO机械安全",
    "ISO公差标准": "ISO公差标准",
    "IEC标准": "IEC标准",
    "DIN标准": "DIN标准",
    "ASME标准": "ASME标准",
    "ASTM标准": "ASTM标准",
    
    # 质量标准
    "MMC": "最大实体条件",
    "LMC": "最小实体条件",
    "GD&T": "几何尺寸与公差",
    "FMEA": "故障模式与影响分析",
    "SPC": "统计过程控制",
    "PPAP": "生产件批准程序",
    "APQP": "产品质量先期策划",
    "ISO 9001": "ISO 9001质量管理体系",
    "iso 9001": "ISO 9001质量管理体系",
    "ISO 14001": "ISO 14001环境管理体系",
    "iso 14001": "ISO 14001环境管理体系",
    "OHSAS 18001": "OHSAS 18001职业健康安全管理体系",
    "ohsas 18001": "OHSAS 18001职业健康安全管理体系",
    "ISO 9000": "ISO 9000质量管理体系",
    "5S": "5S管理",
    "5s": "5S管理",
    "kaizen": "改善",
    "kanban": "看板",
    "poka yoke": "防错",
    "just in time": "准时制生产",
    "zero defect": "零缺陷",
    "quality system": "质量体系",
    "quality plan": "质量计划",
    "quality audit": "质量审核",
    "quality policy": "质量方针",
    "pareto analysis": "帕累托分析",
    "value stream mapping": "价值流图",
    "process capability": "过程能力",
    "measurement system analysis": "测量系统分析",
    "gauge repeatability": "量具重复性",
    "gauge reproducibility": "量具再现性",
    "gauge r and r": "量具R&R分析",
    "statistical quality control": "统计质量控制",
    "foundation": "基础",
    "footing": "基础底板",
    "visual inspection": "目视检验",
    "receiving inspection": "来料检验",
    "functional inspection": "功能检验",
    "ultrasonic inspection": "超声波检测",
    "magnetic particle inspection": "磁粉检测",
    
    # CAD软件
    "AutoCAD": "AutoCAD",
    "SolidWorks": "SolidWorks",
    "CATIA": "CATIA",
    "Creo": "Creo",
    "NX": "NX",
    "Inventor": "Inventor",
    "CAM": "CAM计算机辅助制造",
    "CAD/CAM": "CAD/CAM",
    
    # 制造工艺
    "DFMA": "面向制造与装配的设计",
    "SLM": "选择性激光熔化",
    "FDM": "熔融沉积成型",
    "SLA": "立体光刻成型",
    "PVD": "物理气相沉积",
    "CVD": "化学气相沉积",
    "3D打印": "3D打印",
    "CNC": "CNC数控加工",
    "AGV": "AGV自动导引车",
    "MES": "MES制造执行系统",
    "SCADA": "SCADA数据采集与监控系统",
    "PLC": "PLC可编程逻辑控制器",
    "PCB设计": "PCB设计",
    "S-N曲线": "S-N曲线",
    
    # 材料
    "Metals": "金属材料",
    "steel": "钢",
    "钢": "钢",
    "mild steel": "低碳钢",
    "mild钢": "低碳钢",
    "hotrolled steel": "热轧钢",
    "hotrolled钢": "热轧钢",
    "coldrolled steel": "冷轧钢",
    "coldrolled钢": "冷轧钢",
    "galvanized steel": "镀锌钢",
    "galvanized钢": "镀锌钢",
    "manganese steel": "锰钢",
    "manganese钢": "锰钢",
    "chromium steel": "铬钢",
    "chromium钢": "铬钢",
    "ABS塑料": "ABS塑料",
    "bearings": "轴承",
    "量规bearings": "量规轴承",
    
    # 测试与检测
    "half section": "半剖视图",
    "full section": "全剖视图",
    "removed section": "移出剖面",
    "level gauge": "液位计",
    "tensile testing machine": "拉伸试验机",
    "universal testing machine": "万能试验机",
    "hardness tester": "硬度计",
    "surface roughness tester": "表面粗糙度测量仪",
    "toolmakers microscope": "工具显微镜",
    "profile projector": "轮廓投影仪",
    "optical comparator": "光学比较仪",
    "torque wrench": "扭矩扳手",
    "torque meter": "扭矩计",
    "tachometer": "转速计",
    "stroboscope": "频闪仪",
    "weighing scale": "称重秤",
    "scale": "秤",
    "flow meter": "流量计",
    "rotameter": "转子流量计",
    "venturi meter": "文丘里管",
    "pitot tube": "皮托管",
    "pyrometer": "高温计",
    "thermometer": "温度计",
    "thermistor": "热敏电阻",
    "shaft encoder": "轴编码器",
    "hollow shaft encoder": "空心轴编码器",
    "inductive encoder": "电感式编码器",
    "instrument panel": "仪表盘",
    
    # 力学测试
    "tensile impact test": "拉伸冲击试验",
    "microhardness hardness test": "显微硬度试验",
    "microhardness hardness": "显微硬度",
    "instrumented indentation hardness test": "仪器化压痕硬度试验",
    "instrumented indentation hardness": "仪器化压痕硬度",
    "durometer hardness test": "邵氏硬度试验",
    "scleroscope hardness test": "回弹硬度试验",
    "scleroscope hardness": "回弹硬度",
    "mohs hardness test": "莫氏硬度试验",
    "mohs hardness": "莫氏硬度",
    "knoop hardness test": "努氏硬度试验",
    "knoop hardness": "努氏硬度",
    "shore hardness": "肖氏硬度",
    "shear test": "剪切试验",
    "torsion test": "扭转试验",
    "fold test": "折叠试验",
    "flattening test": "压扁试验",
    "flaring test": "扩口试验",
    "ring expansion test": "环扩试验",
    "formability test": "成形性试验",
    "weldability test": "可焊性试验",
    "hardenability test": "淬透性试验",
    "jominy end quench test": "末端淬火试验",
    "stress rupture test": "应力断裂试验",
    "fracture toughness test": "断裂韧性试验",
    "proof test": "验证试验",
    "shock test": "冲击试验",
    "vibration test": "振动试验",
    "pressure test": "压力试验",
    "hydrostatic test": "静水压试验",
    "pneumatic test": "气动试验",
    "non destructive test": "无损检测",
    "dye penetrant test": "着色渗透检测",
    
    # 力学性能
    "fatigue failure": "疲劳失效",
    "fatigue crack": "疲劳裂纹",
    "stress corrosion cracking": "应力腐蚀开裂",
    "fatigue": "疲劳",
    "elastic deformation": "弹性变形",
    "plastic deformation": "塑性变形",
    "yielding": "屈服",
    "rupture": "断裂",
    "tearing": "撕裂",
    "spalling": "剥落",
    "pitting": "点蚀",
    "fretting": "微动磨损",
    "fretting corrosion": "微动腐蚀",
    "galloseizing": "胶合/咬死",
    "rolling contact fatigue": "滚动接触疲劳",
    "liquid metal embrittlement": "液态金属脆化",
    "hydrogen embrittlement": "氢脆",
    "thermal fatigue": "热疲劳",
    "creep": "蠕变",
    
    # 机器人/自动化
    "scara robot": "SCARA机器人",
    "parallel robot": "并联机器人",
    "wankel engine": "汪克尔发动机",
    "isolation transformer": "隔离变压器",
    "solenoid actuator": "螺线管执行器",
    "piezoelectric actuator": "压电执行器",
    "voice coil actuator": "音圈执行器",
    "shape memory actuator": "形状记忆执行器",
    "thermal actuator": "热执行器",
    "piston actuator": "活塞执行器",
    "motorized actuator": "电动执行器",
    "rack and pinion actuator": "齿条齿轮执行器",
    "low speed": "低速",
    "rated speed": "额定转速",
    "RV减速器": "RV减速器",
    "PID控制": "PID控制",
    
    # 流体/热
    "principal应力": "主应力",
    "maximum应力": "最大应力",
    "hvac系统": "HVAC暖通空调系统",
    "feedwater加热器": "给水加热器",
    "multiphase热转移": "多相传热",
    "stress": "应力",
    "maximum": "最大",
    "润滑": "润滑",
    "forced润滑": "强制润滑",
    "mist润滑": "油雾润滑",
    "centralized润滑": "集中润滑",
    
    # 焊接/成型
    "mig焊接": "MIG熔化极气体保护焊",
    "tig焊接": "TIG钨极气体保护焊",
    "submergedarc焊接": "埋弧焊",
    "forge焊接": "锻焊",
    "welded气缸": "焊接气缸",
    "telescopic气缸": "伸缩气缸",
    "level传感器": "液位传感器",
    "centerless磨削机": "无心磨床",
    "lcd制造": "LCD制造",
    "new制造economy": "新制造经济",
    "open制造": "开放式制造",
    "discrete制造": "离散制造",
    "dynamic制造网络": "动态制造网络",
    "integrated制造database": "集成制造数据库",
    "composites材料": "复合材料",
    "CAD软件概述": "CAD软件概述",
    "CAE仿真概述": "CAE仿真概述",
    
    # 人名
    "Hiroshi Tada（日本学者）": "Hiroshi Tada（田博史）",
    "Hiroshi Tada": "Hiroshi Tada（田博史）",
    "Richard Jenkins（工程专家）": "Richard Jenkins（理查德·詹金斯）",
    "Richard Jenkins": "Richard Jenkins（理查德·詹金斯）",
    
    # 发动机/动力
    "historyofthe射流发动机": "喷气发动机发展史",
    "timelineof喷射功率": "喷射功率发展时间线",
    "convertingsound功率": "声功率转换",
    "horsepowerratings滚子": "滚子额定功率",
    "horsepowerratings工作台": "工作台额定功率",
    "工作台chart功率": "功率表",
    
    # 其他
    "CAD软件概述": "CAD软件概述",
    "CAE仿真概述": "CAE仿真概述",
    "ringsoverview设计guidelines": "环形件设计指南概述",
    "printing设计导向direct金属激光烧结": "直接金属激光烧结设计导向",
    "stdsizes化学阻力计算器径向": "标准尺寸化学阻力计算器",
    "publications注射成型设计导向导向": "注射成型设计导向",
    "end应力concentrationsconsider": "端部应力集中考虑",
    "texture设计elementsribsboss计数器": "纹理设计元素-筋条/凸台计数器",
    "fibrouscomposites设计and": "纤维复合材料设计",
    "selectingcandidate制造工艺程序and": "候选制造工艺程序选择",
    "poisson's比metalsmaterials": "金属材料的泊松比",
    "young's模量of弹性": "杨氏弹性模量",
    "young’s模量of弹性": "杨氏弹性模量",
    "selecting应变量规four": "应变片选择",
    "loan计算器this": "贷款计算器",
    "lease计算器leasing": "租赁计算器",
    "calculations": "计算",
    "calculate": "计算",
    "calculator": "计算器",
    "calculation": "计算",
    "gage": "量规",
    "gauge": "量规",
    "design": "设计",
    "manufacturer": "制造商",
    "manufacturing": "制造",
    "materials": "材料",
    "thermal": "热",
    "stress": "应力",
    "cylinder": "气缸",
    "piston": "活塞",
    "valve": "阀门",
    "pump": "泵",
    "selecting": "选择",
    "four": "",
    "this": "",
    "so": "",
    "and": "",
    "leasing": "",
    "of": "",
    "the": "",
    "a": "",
    "in": "",
    "for": "",
    "to": "",
    "by": "",
    "with": "",
    "motor": "电机",
    "bearing": "轴承",
    "gear": "齿轮",
    "shaft": "轴",
    "spring": "弹簧",
    "fastener": "紧固件",
    "weld": "焊接",
    "joint": "接头",
    "seal": "密封",
    "gasket": "垫片",
    "coupling": "联轴器",
    "clutch": "离合器",
    "brake": "制动器",
    "belt": "皮带",
    "chain": "链条",
    "screw": "螺钉",
    "bolt": "螺栓",
    "nut": "螺母",
    "washer": "垫圈",
    "pin": "销",
    "key": "键",
    "rivet": "铆钉",
    "O型圈": "O型密封圈",
    
    # The American National Standards Institute
    "The American National Standards Institute": "美国国家标准学会",
    
    # 应用详解模式
    "应用详解": "应用详解",
}

# 中文尾缀模式 - 需要保留的中文部分
CHINESE_SUFFIX_PATTERNS = ["—应用详解", "应用详解"]
CHINESE_SUFFIX_RE = re.compile(r'[—\-]?应用详解$')

# 标准变体识别
def clean_title_for_translation(title):
    """Clean title and determine if it has a Chinese suffix like '应用详解'."""
    has_suffix = False
    suffix = ""
    base_title = title
    
    # Check for "—应用详解" or "应用详解" suffix
    m = CHINESE_SUFFIX_RE.search(title)
    if m:
        has_suffix = True
        suffix = m.group(0)
        base_title = title[:m.start()]
    elif "应用详解" in title:
        has_suffix = True
        suffix = "—应用详解"
        base_title = title.replace("应用详解", "").strip("—\- ")
    
    return base_title, suffix, has_suffix

def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]', text))

def is_pure_english(text):
    return not has_chinese(text) and bool(re.search(r'[a-zA-Z]', text))

def is_pure_chinese(text):
    # Allows acronyms, numbers, punctuation mixed with Chinese
    return has_chinese(text)

def normalize_key(key):
    """Normalize dictionary key for matching."""
    return key.strip().lower()

def lookup_translation(text):
    """Look up a phrase in the translation dictionary."""
    # Try exact match first
    if text in TRANSLATION_DICT:
        return TRANSLATION_DICT[text]
    
    # Try lowercase
    lower = text.lower()
    if lower in TRANSLATION_DICT:
        return TRANSLATION_DICT[lower]
    
    # Try title case
    if text.title() in TRANSLATION_DICT:
        return TRANSLATION_DICT[text.title()]
    
    return None

def translate_english_title(title):
    """Translate a pure English title to Chinese."""
    translation = lookup_translation(title)
    if translation:
        return translation
    
    # Split into words and try to translate word by word
    words = title.split()
    translated_words = []
    for w in words:
        t = lookup_translation(w)
        if t:
            translated_words.append(t)
        else:
            # Keep as-is if no translation
            translated_words.append(w)
    
    result = " ".join(translated_words)
    return result

def extract_english_parts(text):
    """Extract English words/segments from mixed text."""
    # Find English segments
    english_parts = re.findall(r'[a-zA-Z]+', text)
    return english_parts

def translate_mixed_title(base_title, suffix=""):
    """Translate mixed Chinese-English title."""
    # First, try direct lookup
    full_key = base_title + suffix
    t = lookup_translation(full_key)
    if t:
        return t
    
    t = lookup_translation(base_title)
    if t:
        return t + suffix if suffix else t
    
    # Handle special patterns
    # Pattern: "EnglishWord中文" -> "中文EnglishWordTranslated"
    # e.g., "量规bearings" -> "量规轴承"
    
    # Try to find English segments and translate them
    # Find English word sequences
    result = base_title
    
    # Find all English segments in order
    english_segments = list(re.finditer(r'[a-zA-Z\s]+', base_title))
    
    # Also find Chinese segments
    chinese_segments = list(re.finditer(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]+', base_title))
    
    if english_segments:
        # Replace English segments with their translations while preserving order
        result_parts = []
        last_end = 0
        
        for match in english_segments:
            eng_text = match.group().strip()
            # Add any text before this English segment
            if match.start() > last_end:
                result_parts.append(base_title[last_end:match.start()])
            
            # Translate the English segment
            translated = lookup_translation(eng_text)
            if translated:
                result_parts.append(translated)
            else:
                # Try individual words
                words = eng_text.split()
                translated_words = []
                for w in words:
                    t = lookup_translation(w)
                    translated_words.append(t if t else w)
                result_parts.append("".join(translated_words))
            
            last_end = match.end()
        
        # Add remaining text after last English segment
        if last_end < len(base_title):
            result_parts.append(base_title[last_end:])
        
        result = "".join(result_parts)
    
    # Clean up: remove duplicated/spurious characters from garbled titles
    result = re.sub(r'\s+', '', result)  # Remove spaces (Chinese doesn't need them)
    
    # Add suffix
    if suffix:
        result = result + suffix
    
    return result

def process_file(filepath, rel_path):
    """Process a single file: translate its title if needed."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Match YAML frontmatter
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None, "No frontmatter"
    
    yaml_block = match.group(1)
    
    # Extract title using regex
    title_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', yaml_block, re.MULTILINE)
    if not title_match:
        return None, "No title in frontmatter"
    
    old_title = title_match.group(1).strip().strip('"').strip("'")
    
    # Determine if translation is needed
    if is_pure_english(old_title):
        # Pure English - translate entirely
        base, suffix, has_suf = clean_title_for_translation(old_title)
        new_title = translate_english_title(base)
        if has_suf and suffix:
            new_title = new_title + suffix
        needs_translation = True
    elif has_chinese(old_title) and bool(re.search(r'[a-zA-Z]', old_title)):
        # Mixed - translate English parts
        base, suffix, has_suf = clean_title_for_translation(old_title)
        new_title = translate_mixed_title(base, suffix if has_suf else "")
        needs_translation = True
    else:
        return None, f"Not needed: {old_title}"
    
    # Skip if no change
    if new_title == old_title:
        return None, f"No change needed: {old_title}"
    
    # Update the title in the file
    old_title_line = title_match.group(0)
    
    # Escape for regex
    escaped_old = re.escape(old_title_line)
    new_title_line = f'title: "{new_title}"'
    
    new_content = re.sub(escaped_old, new_title_line, content, count=1)
    
    if new_content == content:
        return None, f"Failed to update: {old_title} -> {new_title}"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return (rel_path, old_title, new_title), "OK"

def main():
    results = []
    stats = {'pure_english': 0, 'mixed': 0, 'translated': 0, 'errors': 0, 'skipped': 0}
    
    for root, dirs, files in os.walk(CONTENT_DIR):
        for fname in sorted(files):
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, CONTENT_DIR)
            
            result, status = process_file(fpath, rel_path)
            
            if result:
                rel_path, old_title, new_title = result
                results.append((rel_path, old_title, new_title, status))
                if is_pure_english(old_title):
                    stats['pure_english'] += 1
                else:
                    stats['mixed'] += 1
                stats['translated'] += 1
                print(f"✓ {rel_path}: '{old_title}' → '{new_title}'")
            elif status.startswith("Not needed") or status.startswith("No change"):
                stats['skipped'] += 1
            else:
                stats['errors'] += 1
                print(f"✗ {rel_path}: {status}")
    
    # Write report
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("=== M3-P1-2: 标题翻译报告 ===\n\n")
        f.write(f"纯英文标题翻译: {stats['pure_english']} 篇\n")
        f.write(f"中英混杂标题处理: {stats['mixed']} 篇\n")
        f.write(f"翻译总数: {stats['translated']} 篇\n")
        f.write(f"跳过(无需翻译): {stats['skipped']} 篇\n")
        f.write(f"错误: {stats['errors']} 篇\n\n")
        
        f.write("=== 翻译详情 ===\n")
        for rel_path, old_title, new_title, status in results:
            f.write(f"{rel_path}\t{old_title}\t→\t{new_title}\n")
    
    print(f"\n{'='*60}")
    print(f"翻译完成!")
    print(f"纯英文标题翻译: {stats['pure_english']} 篇")
    print(f"中英混杂标题处理: {stats['mixed']} 篇")
    print(f"翻译总数: {stats['translated']} 篇")
    print(f"跳过(无需翻译): {stats['skipped']} 篇")
    print(f"错误: {stats['errors']} 篇")
    print(f"报告已保存: {REPORT_FILE}")

if __name__ == "__main__":
    main()
