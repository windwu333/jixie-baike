#!/usr/bin/env python3
"""
Dry run: preview all title translations without modifying files.
"""
import os
import re

CONTENT_DIR = "/Users/windwu/Desktop/机械师大百科项目/content/website"

# ===== 专业术语词典 (same as translate_titles.py) =====
TRANSLATION_DICT = {
    "DIN": "DIN标准", "EN": "EN标准", "ISO": "ISO标准",
    "iec": "IEC标准", "IEC": "IEC标准",
    "CE": "CE认证", "ce": "CE认证",
    "bs": "BS标准", "gb": "GB标准", "GB": "GB标准",
    "SAE": "SAE标准", "ANSI": "ANSI标准",
    "ASME": "ASME标准", "ASTM": "ASTM标准",
    "nace": "NACE标准", "AWS": "AWS标准",
    "ul": "UL标准", "api": "API标准",
    "ieee": "IEEE标准", "IEEE": "IEEE标准",
    "ATEX": "ATEX防爆认证",
    "GB标准": "GB标准", "JB标准": "JB标准",
    "CE认证": "CE认证", "ISO标准": "ISO标准",
    "ISO机械安全": "ISO机械安全", "ISO公差标准": "ISO公差标准",
    "IEC标准": "IEC标准", "DIN标准": "DIN标准",
    "ASME标准": "ASME标准", "ASTM标准": "ASTM标准",
    "MMC": "最大实体条件", "LMC": "最小实体条件",
    "GD&T": "几何尺寸与公差",
    "FMEA": "故障模式与影响分析", "SPC": "统计过程控制",
    "PPAP": "生产件批准程序", "APQP": "产品质量先期策划",
    "ISO 9001": "ISO 9001质量管理体系",
    "ISO 14001": "ISO 14001环境管理体系",
    "OHSAS 18001": "OHSAS 18001职业健康安全管理体系",
    "5S": "5S管理", "5s": "5S管理",
    "kaizen": "改善", "kanban": "看板",
    "poka yoke": "防错", "just in time": "准时制生产",
    "zero defect": "零缺陷", "quality system": "质量体系",
    "quality plan": "质量计划", "quality audit": "质量审核",
    "quality policy": "质量方针", "pareto analysis": "帕累托分析",
    "value stream mapping": "价值流图", "process capability": "过程能力",
    "measurement system analysis": "测量系统分析",
    "gauge repeatability": "量具重复性",
    "gauge reproducibility": "量具再现性",
    "gauge r and r": "量具R&R分析",
    "statistical quality control": "统计质量控制",
    "foundation": "基础", "footing": "基础底板",
    "visual inspection": "目视检验", "receiving inspection": "来料检验",
    "functional inspection": "功能检验", "ultrasonic inspection": "超声波检测",
    "magnetic particle inspection": "磁粉检测",
    "AutoCAD": "AutoCAD", "SolidWorks": "SolidWorks",
    "CATIA": "CATIA", "Creo": "Creo", "NX": "NX",
    "Inventor": "Inventor", "CAM": "CAM计算机辅助制造",
    "CAD/CAM": "CAD/CAM",
    "DFMA": "面向制造与装配的设计",
    "SLM": "选择性激光熔化", "FDM": "熔融沉积成型",
    "SLA": "立体光刻成型", "PVD": "物理气相沉积",
    "CVD": "化学气相沉积", "3D打印": "3D打印",
    "CNC": "CNC数控加工", "AGV": "AGV自动导引车",
    "MES": "MES制造执行系统", "SCADA": "SCADA数据采集与监控系统",
    "PLC": "PLC可编程逻辑控制器", "PCB设计": "PCB设计",
    "S-N曲线": "S-N曲线",
    "Metals": "金属材料",
    "bearings": "轴承", "量规bearings": "量规轴承",
    "mild steel": "低碳钢", "mild钢": "低碳钢",
    "hotrolled steel": "热轧钢", "hotrolled钢": "热轧钢",
    "coldrolled steel": "冷轧钢", "coldrolled钢": "冷轧钢",
    "galvanized steel": "镀锌钢", "galvanized钢": "镀锌钢",
    "manganese steel": "锰钢", "manganese钢": "锰钢",
    "chromium steel": "铬钢", "chromium钢": "铬钢",
    "ABS塑料": "ABS塑料",
    "half section": "半剖视图", "full section": "全剖视图",
    "removed section": "移出剖面", "level gauge": "液位计",
    "tensile testing machine": "拉伸试验机",
    "universal testing machine": "万能试验机",
    "hardness tester": "硬度计",
    "surface roughness tester": "表面粗糙度测量仪",
    "toolmakers microscope": "工具显微镜",
    "profile projector": "轮廓投影仪",
    "optical comparator": "光学比较仪",
    "torque wrench": "扭矩扳手", "torque meter": "扭矩计",
    "tachometer": "转速计", "stroboscope": "频闪仪",
    "weighing scale": "称重秤", "scale": "秤",
    "flow meter": "流量计", "rotameter": "转子流量计",
    "venturi meter": "文丘里管", "pitot tube": "皮托管",
    "pyrometer": "高温计", "thermometer": "温度计",
    "thermistor": "热敏电阻",
    "shaft encoder": "轴编码器", "hollow shaft encoder": "空心轴编码器",
    "inductive encoder": "电感式编码器", "instrument panel": "仪表盘",
    "tensile impact test": "拉伸冲击试验",
    "microhardness hardness test": "显微硬度试验",
    "microhardness hardness": "显微硬度",
    "instrumented indentation hardness test": "仪器化压痕硬度试验",
    "instrumented indentation hardness": "仪器化压痕硬度",
    "durometer hardness test": "邵氏硬度试验",
    "scleroscope hardness test": "回弹硬度试验",
    "scleroscope hardness": "回弹硬度",
    "mohs hardness test": "莫氏硬度试验", "mohs hardness": "莫氏硬度",
    "knoop hardness test": "努氏硬度试验", "knoop hardness": "努氏硬度",
    "shore hardness": "肖氏硬度",
    "shear test": "剪切试验", "torsion test": "扭转试验",
    "fold test": "折叠试验", "flattening test": "压扁试验",
    "flaring test": "扩口试验", "ring expansion test": "环扩试验",
    "formability test": "成形性试验", "weldability test": "可焊性试验",
    "hardenability test": "淬透性试验",
    "jominy end quench test": "末端淬火试验",
    "stress rupture test": "应力断裂试验",
    "fracture toughness test": "断裂韧性试验",
    "proof test": "验证试验", "shock test": "冲击试验",
    "vibration test": "振动试验", "pressure test": "压力试验",
    "hydrostatic test": "静水压试验", "pneumatic test": "气动试验",
    "non destructive test": "无损检测", "dye penetrant test": "着色渗透检测",
    "fatigue failure": "疲劳失效", "fatigue crack": "疲劳裂纹",
    "stress corrosion cracking": "应力腐蚀开裂",
    "elastic deformation": "弹性变形", "plastic deformation": "塑性变形",
    "yielding": "屈服", "rupture": "断裂", "tearing": "撕裂",
    "spalling": "剥落", "pitting": "点蚀",
    "fretting": "微动磨损", "fretting corrosion": "微动腐蚀",
    "galloseizing": "胶合/咬死", "rolling contact fatigue": "滚动接触疲劳",
    "liquid metal embrittlement": "液态金属脆化",
    "hydrogen embrittlement": "氢脆",
    "thermal fatigue": "热疲劳",
    "scara robot": "SCARA机器人", "parallel robot": "并联机器人",
    "wankel engine": "汪克尔发动机", "isolation transformer": "隔离变压器",
    "solenoid actuator": "螺线管执行器",
    "piezoelectric actuator": "压电执行器",
    "voice coil actuator": "音圈执行器",
    "shape memory actuator": "形状记忆执行器",
    "thermal actuator": "热执行器", "piston actuator": "活塞执行器",
    "motorized actuator": "电动执行器",
    "rack and pinion actuator": "齿条齿轮执行器",
    "low speed": "低速", "rated speed": "额定转速",
    "RV减速器": "RV减速器", "PID控制": "PID控制",
    "principal应力": "主应力", "maximum应力": "最大应力",
    "hvac系统": "HVAC暖通空调系统",
    "feedwater加热器": "给水加热器", "multiphase热转移": "多相传热",
    "forced润滑": "强制润滑", "mist润滑": "油雾润滑",
    "centralized润滑": "集中润滑",
    "mig焊接": "MIG熔化极气体保护焊", "tig焊接": "TIG钨极气体保护焊",
    "submergedarc焊接": "埋弧焊", "forge焊接": "锻焊",
    "welded气缸": "焊接气缸", "telescopic气缸": "伸缩气缸",
    "level传感器": "液位传感器", "centerless磨削机": "无心磨床",
    "lcd制造": "LCD制造", "new制造economy": "新制造经济",
    "open制造": "开放式制造", "discrete制造": "离散制造",
    "dynamic制造网络": "动态制造网络",
    "integrated制造database": "集成制造数据库",
    "composites材料": "复合材料",
    "CAD软件概述": "CAD软件概述", "CAE仿真概述": "CAE仿真概述",
    "Hiroshi Tada": "Hiroshi Tada（田博史）",
    "Richard Jenkins": "Richard Jenkins（理查德·詹金斯）",
    "The American National Standards Institute": "美国国家标准学会",
    "O型圈": "O型密封圈",
    "historyofthe射流发动机": "喷气发动机发展史",
    "timelineof喷射功率": "喷射功率发展时间线",
    "convertingsound功率": "声功率转换",
    "horsepowerratings滚子": "滚子额定功率",
    "horsepowerratings工作台": "工作台额定功率",
    "工作台chart功率": "功率表",
    "ringsoverview设计guidelines": "环形件设计指南概述",
    "printing设计导向direct金属激光烧结": "直接金属激光烧结设计导向",
    "stdsizes化学阻力计算器径向": "标准尺寸化学阻力计算器",
    "publications注射成型设计导向导向": "注射成型设计导向",
    "end应力concentrationsconsider": "端部应力集中考虑",
    "texture设计elementsribsboss计数器": "纹理设计元素-筋条/凸台计数器",
    "fibrouscomposites设计and": "纤维复合材料设计",
    "selectingcandidate制造工艺程序and": "候选制造工艺程序选择",
    "poisson's比metalsmaterials": "金属材料的泊松比",
    "selecting应变量规four": "应变片选择",
    "thermofluid": "热流体", "pneumatic": "气动",
    "hydraulic": "液压", "mechanics": "力学",
    "mechatronics": "机电一体化", "automation": "自动化",
    "manufacturing": "制造", "materials": "材料",
    "measurement": "测量", "quality": "质量",
    "standards": "标准", "design": "设计",
    "testing": "测试", "test": "试验",
    "machine": "机器", "system": "系统",
    "process": "工艺", "analysis": "分析",
    "application": "应用", "control": "控制",
    "embed": "嵌入式", "robot": "机器人",
    "sensor": "传感器", "actuator": "执行器",
    "cylinder": "气缸", "piston": "活塞",
    "valve": "阀门", "pump": "泵",
    "motor": "电机", "engine": "发动机",
    "bearing": "轴承", "gear": "齿轮",
    "shaft": "轴", "spring": "弹簧",
    "fastener": "紧固件", "weld": "焊接",
    "seal": "密封", "coupling": "联轴器",
    "clutch": "离合器", "brake": "制动器",
    "belt": "皮带", "chain": "链条",
    "screw": "螺钉", "bolt": "螺栓",
    "nut": "螺母", "washer": "垫圈",
    "pin": "销", "key": "键",
    "rivet": "铆钉",
    "selecting": "选择", "selection": "选择",
    "four": "",  # Remove stray words
    "this": "", "so": "", "and": "",
    "of": "", "the": "", "a": "", "in": "",
    "for": "", "to": "", "by": "", "with": "",
    "canadianmortgage": "加拿大抵押贷款",
    "loan": "贷款", "lease": "租赁", "leasing": "租赁",
    "currency": "货币", "updated": "更新版",
    "fraction": "分数",
    "register": "注册",
    "cold": "冷端",
    "downstream": "下游",
    "jigs": "夹具",
    "third": "第三",
    "medium": "介质",
    "contact": "接触",
    "approach": "方法",
    "hole": "孔",
    "drilling": "钻孔",
    "dunkerley's": "邓克利",
    "method": "方法",
    "force": "力",
    "compression": "压缩",
    "tension": "拉伸",
    "bending": "弯曲",
    "torque": "扭矩",
    "shear": "剪切",
    "stress": "应力",
    "strain": "应变",
    "modulus": "模量",
    "elasticity": "弹性",
    "young's": "杨氏",
    "young’s": "杨氏",
    "模量": "模量",
    "of": "的",
    "elastic": "弹性",
    "poisson's": "泊松",
    "ratio": "比",
    "metal": "金属",
    "material": "材料",
    "iron": "铁",
    "copper": "铜",
    "aluminum": "铝",
    "zinc": "锌",
    "tin": "锡",
    "lead": "铅",
    "nickel": "镍",
    "titanium": "钛",
    "magnesium": "镁",
    "tungsten": "钨",
    "cobalt": "钴",
    "silicon": "硅",
    "carbon": "碳",
    "alloy": "合金",
    "ceramic": "陶瓷",
    "polymer": "聚合物",
    "composite": "复合材料",
    "fiberglass": "玻璃纤维",
    "reinforced": "增强",
    "thermoplastic": "热塑性",
    "engineering": "工程",
    "塑料": "塑料",
    "fiber": "纤维",
    "fibrous": "纤维",
    "aisi": "AISI",
    "钢identification编号": "钢牌号识别",
    "identification": "识别",
    "编号": "编号",
    "processes机加工": "机加工工艺",
    "formulas力学": "力学公式",
    "mathematicalbasisfor摩擦": "摩擦的数学基础",
    "workingpressures重duty液压connectors": "重型液压连接器工作压力",
    "compressibilityofa流体equationsand": "流体可压缩性方程",
    "steady-stateindoorair质量formulaeand": "稳态室内空气质量公式",
    "swamee-jain摩擦factor方程and": "Swamee-Jain摩擦系数方程",
    "churchill摩擦factorformulaeand": "Churchill摩擦系数公式",
    "statisticalassociating流体theory": "流体统计关联理论",
    "near-fieldradiative热转移": "近场辐射传热",
    "heating,ventilation,andair调节": "暖通空调系统",
    "ljungströmair预热器": "Ljungström空气预热器",
    "maximum材料条件": "最大材料条件",
    "sixsigmaforelectronics设计": "六西格玛电子设计",
    "nasa工程拉深standards": "NASA工程拉深标准",
    "aerospaceapplications结构的": "航空航天结构应用",
    "materials压力容器": "压力容器材料",
    "calculator压力容器": "压力容器计算器",
    "压力容器external": "外部压力容器",
    "压力容器external压力calculations": "压力容器外部压力计算",
    "5Why分析法": "5Why分析法",
    "线材仪表sizes": "线材尺寸规格",
    "gdt包络principlerulesimulator": "GD&T包络原则规则模拟器",
    "shell-MIT": "Shell-MIT换热器",
    "tesla自动化": "特斯拉自动化",
    "factor": "系数",
    "equation": "方程",
    "formula": "公式",
    "formulae": "公式",
    "equations": "方程",
}

CHINESE_SUFFIX_RE = re.compile(r'[—\-]?应用详解$')

def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]', text))

def is_pure_english(text):
    return not has_chinese(text) and bool(re.search(r'[a-zA-Z]', text))

def lookup_translation(text):
    if text in TRANSLATION_DICT:
        return TRANSLATION_DICT[text]
    lower = text.lower()
    if lower in TRANSLATION_DICT:
        return TRANSLATION_DICT[lower]
    if text.title() in TRANSLATION_DICT:
        return TRANSLATION_DICT[text.title()]
    return None

def translate_english_title(title):
    translation = lookup_translation(title)
    if translation:
        return translation
    words = title.split()
    translated_words = []
    for w in words:
        t = lookup_translation(w)
        if t:
            translated_words.append(t)
        else:
            translated_words.append(w)
    return "".join(translated_words)

def translate_mixed_title(base_title):
    result = base_title
    english_segments = list(re.finditer(r'[a-zA-Z\s]+', base_title))
    
    if not english_segments:
        return base_title
    
    result_parts = []
    last_end = 0
    
    for match in english_segments:
        eng_text = match.group().strip()
        if match.start() > last_end:
            result_parts.append(base_title[last_end:match.start()])
        
        translated = lookup_translation(eng_text)
        if translated:
            result_parts.append(translated)
        else:
            words = eng_text.split()
            translated_words = []
            for w in words:
                t = lookup_translation(w)
                translated_words.append(t if t else w)
            result_parts.append("".join(translated_words))
        
        last_end = match.end()
    
    if last_end < len(base_title):
        result_parts.append(base_title[last_end:])
    
    result = "".join(result_parts)
    result = re.sub(r'\s+', '', result)
    return result

def extract_title(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None
    title_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', match.group(1), re.MULTILINE)
    if title_match:
        return title_match.group(1).strip().strip('"').strip("'")
    return None

def get_new_title(title):
    if is_pure_english(title):
        base, suffix, has_suf = title, "", False
        m = CHINESE_SUFFIX_RE.search(title)
        if m:
            has_suf = True
            suffix = m.group(0)
            base = title[:m.start()]
        new_title = translate_english_title(base)
        if has_suf and suffix:
            new_title = new_title + suffix
        return new_title
    elif has_chinese(title) and bool(re.search(r'[a-zA-Z]', title)):
        base, suffix, has_suf = title, "", False
        m = CHINESE_SUFFIX_RE.search(title)
        if m:
            has_suf = True
            suffix = m.group(0)
            base = title[:m.start()]
        
        # Try full lookup first
        t = lookup_translation(title)
        if t:
            return t
        t = lookup_translation(base)
        if t and has_suf:
            return t + suffix
        
        new_title = translate_mixed_title(base)
        if has_suf and suffix:
            new_title = new_title + suffix
        return new_title
    return title

# Main dry run
stats = {'pure_english': 0, 'mixed': 0, 'changed': 0, 'no_change': 0, 'errors': 0}
changes = []

for root, dirs, files in os.walk(CONTENT_DIR):
    for fname in sorted(files):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(root, fname)
        rel_path = os.path.relpath(fpath, CONTENT_DIR)
        
        title = extract_title(fpath)
        if title is None:
            stats['errors'] += 1
            continue
        
        if is_pure_english(title):
            stats['pure_english'] += 1
        elif has_chinese(title) and bool(re.search(r'[a-zA-Z]', title)):
            stats['mixed'] += 1
        else:
            stats['no_change'] += 1
            continue
        
        new_title = get_new_title(title)
        if new_title != title:
            stats['changed'] += 1
            changes.append((rel_path, title, new_title))

print(f"=== 翻译预览 ===\n")
print(f"纯英文标题: {stats['pure_english']}")
print(f"中英混杂标题: {stats['mixed']}")
print(f"需要改动: {stats['changed']}")
print(f"无需改动(已匹配): {stats['pure_english'] + stats['mixed'] - stats['changed']}")
print(f"\n共 {len(changes)} 篇需要修改:\n")

# Group by type for review
pure_changes = [(p, o, n) for p, o, n in changes if is_pure_english(o)]
mixed_changes = [(p, o, n) for p, o, n in changes if not is_pure_english(o)]

print(f"--- 纯英文 → 中文 ({len(pure_changes)} 篇) ---")
for path, old, new in pure_changes:
    print(f"  {path}: '{old}' → '{new}'")

print(f"\n--- 中英混杂 → 纯中文 ({len(mixed_changes)} 篇) ---")
for path, old, new in mixed_changes:
    print(f"  {path}: '{old}' → '{new}'")

# Save full preview
preview_path = "/Users/windwu/Desktop/机械师大百科项目/title_translation_preview.txt"
with open(preview_path, 'w', encoding='utf-8') as f:
    f.write(f"=== 翻译预览 ===\n")
    f.write(f"纯英文标题: {stats['pure_english']}\n")
    f.write(f"中英混杂标题: {stats['mixed']}\n")
    f.write(f"需要改动: {stats['changed']}\n\n")
    f.write("--- 纯英文 → 中文 ---\n")
    for path, old, new in pure_changes:
        f.write(f"{path}\t{old}\t→\t{new}\n")
    f.write("\n--- 中英混杂 → 纯中文 ---\n")
    for path, old, new in mixed_changes:
        f.write(f"{path}\t{old}\t→\t{new}\n")

print(f"\n预览已保存: {preview_path}")
