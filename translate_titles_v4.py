#!/usr/bin/env python3
"""
M3-P1-2 v4: 终极修复版
直接从原始标题报告读取，强制更新每个文件为正确翻译。
"""
import os
import re

CONTENT_DIR = "/Users/windwu/Desktop/机械师大百科项目/content/website"
REPORT_FILE = "/Users/windwu/Desktop/机械师大百科项目/title_translation_final_report.txt"

# ===== 完整翻译词典（同v3）=====
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
    "MMC": "最大实体条件", "LMC": "最小实体条件",
    "GD&T": "几何尺寸与公差",
    "FMEA": "故障模式与影响分析", "SPC": "统计过程控制",
    "PPAP": "生产件批准程序", "APQP": "产品质量先期策划",
    "ISO 9001": "ISO 9001质量管理体系", "iso 9001": "ISO 9001质量管理体系",
    "ISO 14001": "ISO 14001环境管理体系", "iso 14001": "ISO 14001环境管理体系",
    "OHSAS 18001": "OHSAS 18001职业健康安全管理体系",
    "ohsas 18001": "OHSAS 18001职业健康安全管理体系",
    "ISO 9000": "ISO 9000质量管理体系",
    "5S": "5S管理", "5s": "5S管理",
    "kaizen": "改善", "kanban": "看板",
    "poka yoke": "防错", "just in time": "准时制生产",
    "zero defect": "零缺陷", "quality system": "质量体系",
    "quality plan": "质量计划", "quality audit": "质量审核",
    "quality policy": "质量方针", "pareto analysis": "帕累托分析",
    "value stream mapping": "价值流图", "process capability": "过程能力",
    "measurement system analysis": "测量系统分析",
    "gauge repeatability": "量具重复性", "gauge reproducibility": "量具再现性",
    "gauge r and r": "量具R&R分析", "statistical quality control": "统计质量控制",
    "foundation": "基础", "footing": "基础底板",
    "visual inspection": "目视检验", "receiving inspection": "来料检验",
    "functional inspection": "功能检验", "ultrasonic inspection": "超声波检测",
    "magnetic particle inspection": "磁粉检测",
    "AutoCAD": "AutoCAD", "SolidWorks": "SolidWorks", "CATIA": "CATIA",
    "Creo": "Creo", "NX": "NX", "Inventor": "Inventor",
    "CAM": "CAM计算机辅助制造", "CAD/CAM": "CAD/CAM",
    "DFMA": "面向制造与装配的设计",
    "SLM": "选择性激光熔化", "FDM": "熔融沉积成型", "SLA": "立体光刻成型",
    "PVD": "物理气相沉积", "CVD": "化学气相沉积",
    "Metals": "金属材料",
    "mild steel": "低碳钢", "mild钢": "低碳钢",
    "hotrolled steel": "热轧钢", "hotrolled钢": "热轧钢",
    "coldrolled steel": "冷轧钢", "coldrolled钢": "冷轧钢",
    "galvanized steel": "镀锌钢", "galvanized钢": "镀锌钢",
    "manganese steel": "锰钢", "manganese钢": "锰钢",
    "chromium steel": "铬钢", "chromium钢": "铬钢",
    "bearings": "轴承", "量规bearings": "量规轴承",
    "half section": "半剖视图", "full section": "全剖视图",
    "removed section": "移出剖面", "level gauge": "液位计",
    "tensile testing machine": "拉伸试验机", "universal testing machine": "万能试验机",
    "hardness tester": "硬度计", "surface roughness tester": "表面粗糙度测量仪",
    "toolmakers microscope": "工具显微镜", "profile projector": "轮廓投影仪",
    "optical comparator": "光学比较仪",
    "torque wrench": "扭矩扳手", "torque meter": "扭矩计",
    "tachometer": "转速计", "stroboscope": "频闪仪",
    "weighing scale": "称重秤", "scale": "秤",
    "flow meter": "流量计", "rotameter": "转子流量计",
    "venturi meter": "文丘里管", "pitot tube": "皮托管",
    "pyrometer": "高温计", "thermometer": "温度计", "thermistor": "热敏电阻",
    "shaft encoder": "轴编码器", "hollow shaft encoder": "空心轴编码器",
    "inductive encoder": "电感式编码器", "instrument panel": "仪表盘",
    "tensile impact test": "拉伸冲击试验",
    "microhardness hardness test": "显微硬度试验", "microhardness hardness": "显微硬度",
    "instrumented indentation hardness test": "仪器化压痕硬度试验",
    "instrumented indentation hardness": "仪器化压痕硬度",
    "durometer hardness test": "邵氏硬度试验",
    "scleroscope hardness test": "回弹硬度试验", "scleroscope hardness": "回弹硬度",
    "mohs hardness test": "莫氏硬度试验", "mohs hardness": "莫氏硬度",
    "knoop hardness test": "努氏硬度试验", "knoop hardness": "努氏硬度",
    "shore hardness": "肖氏硬度",
    "shear test": "剪切试验", "torsion test": "扭转试验",
    "fold test": "折叠试验", "flattening test": "压扁试验",
    "flaring test": "扩口试验", "ring expansion test": "环扩试验",
    "formability test": "成形性试验", "weldability test": "可焊性试验",
    "hardenability test": "淬透性试验", "jominy end quench test": "末端淬火试验",
    "stress rupture test": "应力断裂试验", "fracture toughness test": "断裂韧性试验",
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
    "liquid metal embrittlement": "液态金属脆化", "hydrogen embrittlement": "氢脆",
    "thermal fatigue": "热疲劳",
    "AGV": "AGV自动导引车", "MES": "MES制造执行系统",
    "SCADA": "SCADA数据采集与监控系统", "PLC": "PLC可编程逻辑控制器",
    "scara robot": "SCARA机器人", "parallel robot": "并联机器人",
    "wankel engine": "汪克尔发动机", "isolation transformer": "隔离变压器",
    "solenoid actuator": "螺线管执行器", "piezoelectric actuator": "压电执行器",
    "voice coil actuator": "音圈执行器", "shape memory actuator": "形状记忆执行器",
    "thermal actuator": "热执行器", "piston actuator": "活塞执行器",
    "motorized actuator": "电动执行器", "rack and pinion actuator": "齿条齿轮执行器",
    "low speed": "低速", "rated speed": "额定转速",
    "Hiroshi Tada（日本学者）": "Hiroshi Tada（田博史）",
    "Hiroshi Tada": "Hiroshi Tada（田博史）",
    "Richard Jenkins（工程专家）": "Richard Jenkins（理查德·詹金斯）",
    "Richard Jenkins": "Richard Jenkins（理查德·詹金斯）",
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
    "young's模量of弹性": "杨氏弹性模量",
    "young’s模量of弹性": "杨氏弹性模量",
    "selecting应变量规four": "应变片选择",
    "loan计算器this": "贷款计算器",
    "lease计算器leasing": "租赁计算器",
    "The American National Standards Institute": "美国国家标准学会",
    "O型圈": "O型密封圈",
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
    "mathematicalbasisfor摩擦": "摩擦的数学基础",
    "workingpressures重duty液压connectors": "重型液压连接器工作压力",
    "compressibilityofa流体equationsand": "流体可压缩性方程",
    "steady-stateindoorair质量formulaeand": "稳态室内空气质量公式",
    "swamee-jain摩擦factor方程and": "Swamee-Jain摩擦系数方程",
    "churchill摩擦factorformulaeand": "Churchill摩擦系数公式",
    "statisticalassociating流体theory": "流体统计关联理论",
    "heating,ventilation,andair调节": "暖通空调系统",
    "ljungströmair预热器": "Ljungström空气预热器",
    "maximum材料条件": "最大材料条件",
    "aisi/钢identification编号": "AISI/钢识别编号",
    "tesla自动化": "特斯拉自动化",
    "hole钻孔方法": "孔钻孔方法",
    "third介质接触方法": "第三介质接触方法",
    "dunkerley's方法": "邓克利方法",
    "mist润滑": "油雾润滑",
    "forced润滑": "强制润滑",
    "centralized润滑": "集中润滑",
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
    "principal应力": "主应力",
    "maximum应力": "最大应力",
    "hvac系统": "HVAC暖通空调系统",
    "feedwater加热器": "给水加热器",
    "multiphase热转移": "多相传热",
    "near-fieldradiative热转移": "近场辐射传热",
    "processes机加工": "机加工工艺",
    "formulas力学": "力学公式",
    "calculator": "计算器",
    "canadianmortgage计算器": "加拿大抵押贷款计算器",
    "currency计算器updated": "货币计算器更新版",
    "fraction计算器设计": "分数计算器设计",
}

WORD_DICT = {
    "and": "", "of": "", "the": "", "a": "", "an": "",
    "in": "", "for": "", "to": "", "by": "", "with": "",
    "this": "", "so": "", "four": "", "leasing": "",
    "jigs": "夹具", "downstream": "下游", "register": "注册",
    "cold": "冷端", "selecting": "",
    "processes": "工艺", "formulas": "公式",
    "calculations": "计算", "calculate": "计算",
    "calculation": "计算", "gage": "量规", "gauge": "量规",
    "design": "设计", "manufacturing": "制造",
    "materials": "材料", "thermal": "热",
    "stress": "应力", "cylinder": "气缸",
    "piston": "活塞", "valve": "阀门", "pump": "泵",
    "motor": "电机", "bearing": "轴承",
    "gear": "齿轮", "shaft": "轴",
    "spring": "弹簧", "fastener": "紧固件",
    "weld": "焊接", "seal": "密封",
    "maximum": "最大", "minimum": "最小",
    "currency": "货币", "updated": "更新版",
    "fraction": "分数",
    "loan": "贷款", "lease": "租赁",
    "dynamic": "动态", "static": "静态",
}

def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]', text))

def is_pure_english(text):
    return not has_chinese(text) and bool(re.search(r'[a-zA-Z]', text))

def lookup(t):
    if t in TRANSLATION_DICT:
        return TRANSLATION_DICT[t]
    lt = t.lower()
    if lt in TRANSLATION_DICT:
        return TRANSLATION_DICT[lt]
    return None

def translate_pure(title):
    t = lookup(title)
    if t:
        return t
    words = title.split()
    parts = []
    for w in words:
        t2 = lookup(w)
        if t2:
            parts.append(t2)
        elif w.lower() in WORD_DICT:
            v = WORD_DICT[w.lower()]
            if v:
                parts.append(v)
        else:
            parts.append(w)
    return " ".join(parts).strip()

def translate_mixed(title):
    t = lookup(title)
    if t:
        return t
    segs = list(re.finditer(r'[a-zA-Z\s]+', title))
    if not segs:
        return None
    parts = []
    last = 0
    for m in segs:
        eng = m.group().strip()
        if not eng:
            continue
        if m.start() > last:
            parts.append(title[last:m.start()])
        t2 = lookup(eng)
        if t2:
            parts.append(t2)
        else:
            sw = eng.split()
            sp = []
            for w in sw:
                t3 = lookup(w)
                if t3:
                    sp.append(t3)
                elif w.lower() in WORD_DICT:
                    v = WORD_DICT[w.lower()]
                    if v:
                        sp.append(v)
                else:
                    sp.append(w)
            parts.append("".join(sp))
        last = m.end()
    if last < len(title):
        parts.append(title[last:])
    result = "".join(parts)
    result = re.sub(r'\s+', '', result)
    return result

def get_translation(title):
    """Get translation for any title."""
    # Handle "—应用详解" suffix
    suffix = ""
    base = title
    sm = re.search(r'[—\-]?应用详解$', title)
    if sm:
        suffix = sm.group(0)
        base = title[:sm.start()]
    
    if is_pure_english(title):
        new_base = translate_pure(base)
    elif has_chinese(title) and re.search(r'[a-zA-Z]', title):
        new_base = translate_mixed(base)
    else:
        return None
    
    result = new_base + suffix if suffix else new_base
    if result == title:
        return None
    return result

def read_original_titles():
    """Read original titles from first report."""
    orig = {}
    path = "/Users/windwu/Desktop/机械师大百科项目/english_titles_report.txt"
    in_pure = in_mixed = False
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if "纯英文标题" in line and "===" in line:
                in_pure = True; in_mixed = False; continue
            if "中英混杂标题" in line and "===" in line:
                in_pure = False; in_mixed = True; continue
            if (in_pure or in_mixed) and '\t' in line:
                p, t = line.split('\t', 1)
                orig[p] = t
    return orig

def main():
    # Get original titles
    orig_titles = read_original_titles()
    print(f"从报告读取 {len(orig_titles)} 篇原始标题")
    
    stats = {'translated': 0, 'unchanged': 0, 'error': 0}
    changes = []
    
    for root, dirs, files in os.walk(CONTENT_DIR):
        for fname in sorted(files):
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, CONTENT_DIR)
            
            if rel_path not in orig_titles:
                continue
            
            old_title = orig_titles[rel_path]
            new_title = get_translation(old_title)
            
            if new_title is None:
                stats['unchanged'] += 1
                continue
            
            # Force-update the title line in the file regardless of current content
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find current title line in frontmatter
            m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
            if not m:
                stats['error'] += 1
                print(f"✗ {rel_path}: No frontmatter")
                continue
            
            yaml_block = m.group(1)
            # Match any title line (existing/current)
            tm = re.search(r'^title:\s*.*$', yaml_block, re.MULTILINE)
            if not tm:
                stats['error'] += 1
                print(f"✗ {rel_path}: No title line")
                continue
            
            old_line = tm.group(0)
            new_line = f'title: "{new_title}"'
            
            new_content = re.sub(re.escape(old_line), new_line, content, count=1)
            if new_content == content:
                stats['error'] += 1
                print(f"✗ {rel_path}: Failed to replace")
                continue
            
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            stats['translated'] += 1
            changes.append((rel_path, old_title, new_title))
            
            # Show only if different from expected
            expected_title_part = old_title[:40]
            print(f"✓ {rel_path}: '{old_title}' → '{new_title}'")
    
    # Write report
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"=== M3-P1-2 标题翻译报告 ===\n")
        f.write(f"翻译: {stats['translated']}\n")
        f.write(f"无需变更: {stats['unchanged']}\n")
        f.write(f"错误: {stats['error']}\n\n")
        f.write("=== 翻译详情 ===\n")
        for p, o, n in changes:
            f.write(f"{p}\t{o}\t→\t{n}\n")
    
    print(f"\n翻译完成: {stats['translated']} 篇, 跳过: {stats['unchanged']}, 错误: {stats['error']}")

if __name__ == "__main__":
    main()
