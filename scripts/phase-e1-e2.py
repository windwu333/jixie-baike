#!/usr/bin/env python3
"""Phase E1+E2: 批量修正术语偏差 + 自动补齐未翻译术语

Pipeline:
  1. 加载 v4 术语表和验证报告
  2. 批量修正 30 条术语偏差 (E1)
  3. 构建翻译生成器: 参考词典 + 词级组合 + 模式匹配
  4. 为未翻译/部分翻译术语生成中文 (E2)
  5. 输出修正后的 v5 术语表

用法: python3 scripts/phase-e1-e2.py
"""
import json, re, sys
from pathlib import Path
from collections import defaultdict, Counter

BASE = Path(__file__).parent.parent
KB = BASE / "knowledge-base"

# ── Phase E1: 30 条术语偏差修正规则 ──
# 格式: { "en": "标准中文" }
E1_CORRECTIONS = {
    "orthographic projection": "正投影",
    "continuous casting": "连铸",
    "shear strain": "切应变",
    "shear stress": "切应力",
    "ductility": "延性",
    "shear modulus": "切变模量",
    "PLC": "可编程控制器",
    "bending": "弯曲",
    "bill of materials": "明细栏",
    "closed die forging": "闭式模锻",
    "gate": "内浇口",
    "thermal conductivity": "导热系数",
    "seal": "密封件",
    "valve": "阀",
    "actuator": "执行元件",
    "proximity sensor": "接近传感器",
    "servo motor": "伺服电动机",
    "stepper motor": "步进电动机",
    "GB standard": "国家标准",
    "ISO standard": "国际标准",
    "turbine": "涡轮",
    "viscosity": "黏度",
    "Backlash": "侧隙",
    "Coordinate Measuring Machine": "坐标测量机",
    "laser welding": "激光焊",
    "ultrasonic welding": "超声波焊",
    "friction welding": "摩擦焊",
    "resistance welding": "电阻焊",
    "electron beam welding": "电子束焊",
    "gas welding": "气焊",
}


def load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_bytes())


def build_translation_engine():
    """Build a translation engine from all verified/reference terms

    Returns:
        term_dict: { en_lower: zh } — exact term translations
        word_dict: { en_word: zh_word } — word-level translation
        pattern_rules: list of (regex, zh_template) for common patterns
    """
    term_dict = {}  # en_lower → zh (exact)
    word_dict = {}  # word → zh candidate (for composition)

    # 1. Seed terms + supplement (highest quality)
    supplement = load_json(KB / "mech-supplement.json")
    if supplement and isinstance(supplement, list):
        for t in supplement:
            en = t.get("en", "").strip().lower()
            zh = t.get("zh", "").strip()
            if en and zh:
                term_dict[en] = zh

    # 2. Canonical translations (inline from terminology-verification.py)
    canonical = {
        "torque": "转矩", "torsion": "扭转", "torsional stress": "扭转应力",
        "bending": "弯曲", "bending moment": "弯矩", "shear": "剪切",
        "shear stress": "切应力", "shear strain": "切应变",
        "normal stress": "正应力", "principal stress": "主应力",
        "stress concentration": "应力集中",
        "fatigue": "疲劳", "fatigue strength": "疲劳强度",
        "yield strength": "屈服强度", "tensile strength": "抗拉强度",
        "compressive strength": "抗压强度", "elastic modulus": "弹性模量",
        "shear modulus": "切变模量", "poisson's ratio": "泊松比",
        "hardness": "硬度", "toughness": "韧性", "ductility": "延性",
        "pitch": "齿距", "pitch circle": "分度圆", "module": "模数",
        "gear ratio": "传动比", "backlash": "侧隙",
        "addendum": "齿顶高", "dedendum": "齿根高",
        "tooth profile": "齿廓", "involute": "渐开线",
        "pressure angle": "压力角", "contact ratio": "重合度",
        "pitting": "点蚀", "pitting resistance": "接触强度",
        "planetary gear": "行星齿轮", "sun gear": "太阳轮", "ring gear": "齿圈",
        "plain bearing": "滑动轴承", "rolling bearing": "滚动轴承",
        "ball bearing": "球轴承", "roller bearing": "滚子轴承",
        "thrust bearing": "推力轴承",
        "annealing": "退火", "normalizing": "正火", "quenching": "淬火",
        "tempering": "回火", "aging": "时效",
        "welding": "焊接", "brazing": "硬钎焊", "soldering": "软钎焊",
        "arc welding": "电弧焊",
        "resistance welding": "电阻焊", "friction welding": "摩擦焊",
        "forging": "锻造", "die forging": "模锻", "open die forging": "自由锻",
        "hot forging": "热锻", "cold forging": "冷锻",
        "casting": "铸造", "sand casting": "砂型铸造", "die casting": "压铸",
        "orthographic projection": "正投影", "isometric view": "轴测图",
        "section view": "剖视图", "detail view": "局部放大图",
        "exploded view": "爆炸图", "datum": "基准", "tolerance": "公差",
        "thermodynamics": "热力学", "heat transfer": "传热",
        "fluid mechanics": "流体力学", "viscosity": "黏度",
        "laminar flow": "层流", "turbulent flow": "湍流",
        "boundary layer": "边界层", "reynolds number": "雷诺数",
        "enthalpy": "焓", "entropy": "熵", "specific heat": "比热容",
        "thermal conductivity": "导热系数",
        "sensor": "传感器", "actuator": "执行元件",
        "servo motor": "伺服电动机", "stepper motor": "步进电动机",
        "encoder": "编码器", "solenoid": "电磁铁",
        "proximity sensor": "接近传感器", "plc": "可编程控制器",
        "steel": "钢", "cast iron": "铸铁", "carbon steel": "碳钢",
        "alloy steel": "合金钢", "stainless steel": "不锈钢",
        "tool steel": "工具钢", "aluminum alloy": "铝合金",
        "composite material": "复合材料", "ceramic": "陶瓷",
        "polymer": "聚合物", "corrosion": "腐蚀",
        "internal combustion engine": "内燃机", "gas turbine": "燃气轮机",
        "steam turbine": "汽轮机", "compressor": "压缩机",
        "hydraulic system": "液压系统", "pneumatic system": "气动系统",
        "pump": "泵", "valve": "阀", "piston": "活塞", "seal": "密封件",
        "caliper": "卡尺", "micrometer": "千分尺", "gauge": "量规",
        "yield point": "屈服点", "ultimate strength": "强度极限",
        "young's modulus": "杨氏模量",
        "case hardening": "表面硬化", "hardenability": "淬透性",
        "ultrasonic welding": "超声波焊", "laser welding": "激光焊",
        "electron beam welding": "电子束焊",
        "butt joint": "对接接头", "lap joint": "搭接接头",
        "heat affected zone": "热影响区", "base metal": "母材",
        "closed die forging": "闭式模锻",
        "mold": "铸型", "core": "型芯", "riser": "冒口",
        "shrinkage": "缩孔", "porosity": "气孔",
        "first angle projection": "第一角投影", "third angle projection": "第三角投影",
        "scale": "比例", "title block": "标题栏", "bill of materials": "明细栏",
        "mach number": "马赫数", "bernoulli's principle": "伯努利原理",
        "relay": "继电器", "microcontroller": "微控制器",
        "elastomer": "弹性体",
        "nozzle": "喷嘴", "propeller": "螺旋桨",
        "cylinder": "缸", "accumulator": "蓄能器", "filter": "过滤器",
        "coordinate measuring machine": "坐标测量机",
    }
    for en_lower, zh_std in canonical.items():
        term_dict[en_lower] = zh_std

    # 3. All v4 terms with verified-good zh
    v4 = load_json(KB / "mech-terminology-v4.json")
    if v4:
        for t in v4.get("terms", []):
            en = t.get("en", "").strip().lower()
            zh = t.get("zh", "").strip()
            src = t.get("source", "")

            # Only use terms with good translations
            if not zh or len(zh) < 2:
                continue
            has_ascii = any(c.isascii() and c.isalpha() for c in zh)
            if has_ascii:
                continue
            if zh == en:
                continue
            if en not in term_dict:
                term_dict[en] = zh

    # 4. Build word-level dictionary from verified terms
    #    Split multi-word terms into individual words and map to zh
    for en_lower, zh in term_dict.items():
        words = en_lower.split()
        if len(words) <= 1:
            # Single word: the whole term is the word translation
            word_dict[en_lower] = zh
        else:
            # Multi-word: for each word, check if there's a known mapping
            # Try to split zh into corresponding parts (simple heuristic)
            for w in words:
                if w not in word_dict and len(w) >= 2:
                    # Skip — word_dict is manually populated with known translations
                    pass

    # 5. Manual word translations for common components
    word_dict.update({
        # Materials
        "steel": "钢",
        "iron": "铁",
        "aluminum": "铝",
        "copper": "铜",
        "zinc": "锌",
        "tin": "锡",
        "lead": "铅",
        "nickel": "镍",
        "chromium": "铬",
        "molybdenum": "钼",
        "titanium": "钛",
        "vanadium": "钒",
        "tungsten": "钨",
        "cobalt": "钴",
        "manganese": "锰",
        "silicon": "硅",
        "carbon": "碳",
        "alloy": "合金",
        "metal": "金属",
        "plastic": "塑料",
        "ceramic": "陶瓷",
        "composite": "复合材料",
        "polymer": "聚合物",
        "rubber": "橡胶",
        "wood": "木材",
        "glass": "玻璃",

        # Process
        "casting": "铸造",
        "forging": "锻造",
        "welding": "焊接",
        "machining": "加工",
        "milling": "铣削",
        "turning": "车削",
        "drilling": "钻孔",
        "grinding": "磨削",
        "cutting": "切削",
        "forming": "成形",
        "rolling": "轧制",
        "extrusion": "挤压",
        "drawing": "拉拔",
        "punching": "冲压",
        "stamping": "冲压",
        "bending": "弯曲",
        "shearing": "剪切",
        "annealing": "退火",
        "tempering": "回火",
        "quenching": "淬火",
        "normalizing": "正火",
        "hardening": "硬化",
        "plating": "镀",
        "coating": "涂层",
        "polishing": "抛光",
        "heat": "热",
        "treat": "处理",
        "treatment": "处理",

        # Machine elements
        "gear": "齿轮",
        "bearing": "轴承",
        "shaft": "轴",
        "spring": "弹簧",
        "screw": "螺钉",
        "bolt": "螺栓",
        "nut": "螺母",
        "washer": "垫圈",
        "pin": "销",
        "key": "键",
        "coupling": "联轴器",
        "clutch": "离合器",
        "brake": "制动器",
        "belt": "带",
        "chain": "链",
        "cam": "凸轮",
        "valve": "阀",
        "pump": "泵",
        "seal": "密封",
        "ring": "环",
        "plate": "板",
        "pipe": "管",
        "tube": "管",
        "rod": "杆",
        "bar": "棒",
        "wire": "线材",
        "sheet": "板料",
        "strip": "带材",

        # Mechanics
        "stress": "应力",
        "strain": "应变",
        "force": "力",
        "load": "载荷",
        "torque": "转矩",
        "moment": "矩",
        "pressure": "压力",
        "temperature": "温度",
        "velocity": "速度",
        "acceleration": "加速度",
        "frequency": "频率",
        "amplitude": "振幅",
        "displacement": "位移",
        "vibration": "振动",
        "fatigue": "疲劳",
        "fracture": "断裂",
        "corrosion": "腐蚀",
        "wear": "磨损",
        "friction": "摩擦",
        "lubrication": "润滑",
        "strength": "强度",
        "hardness": "硬度",
        "toughness": "韧性",
        "modulus": "模量",
        "ratio": "比",
        "coefficient": "系数",
        "factor": "因子",
        "efficiency": "效率",

        # Thermal
        "thermal": "热",
        "temperature": "温度",
        "heat": "热",
        "flow": "流动",
        "fluid": "流体",
        "gas": "气体",
        "liquid": "液体",
        "steam": "蒸汽",
        "air": "空气",
        "water": "水",
        "oil": "油",
        "coolant": "冷却剂",
        "lubricant": "润滑剂",

        # Electrical / Control
        "motor": "电动机",
        "sensor": "传感器",
        "actuator": "执行器",
        "controller": "控制器",
        "encoder": "编码器",
        "transducer": "换能器",
        "solenoid": "电磁阀",
        "relay": "继电器",
        "switch": "开关",
        "circuit": "电路",
        "voltage": "电压",
        "current": "电流",
        "power": "功率",
        "signal": "信号",
        "feedback": "反馈",

        # Measurement
        "measurement": "测量",
        "gauge": "量规",
        "caliper": "卡尺",
        "micrometer": "千分尺",
        "indicator": "指示表",
        "inspection": "检验",
        "test": "试验",
        "testing": "试验",
        "analysis": "分析",
        "calculation": "计算",
        "design": "设计",
        "model": "模型",
        "simulation": "仿真",

        # Dimensions / Geometry
        "length": "长度",
        "width": "宽度",
        "height": "高度",
        "depth": "深度",
        "diameter": "直径",
        "radius": "半径",
        "angle": "角度",
        "area": "面积",
        "volume": "体积",
        "mass": "质量",
        "weight": "重量",
        "density": "密度",
        "surface": "表面",
        "edge": "棱边",
        "corner": "角",
        "thread": "螺纹",

        # General mechanical
        "machine": "机器",
        "mechanism": "机构",
        "system": "系统",
        "device": "装置",
        "equipment": "设备",
        "tool": "工具",
        "component": "零件",
        "part": "零件",
        "assembly": "装配",
        "unit": "单元",
        "structure": "结构",
        "frame": "机架",
        "housing": "壳体",
        "cover": "盖",
        "base": "底座",
        "support": "支架",
        "holder": "夹具",
        "fixture": "夹具",
        "jig": "夹具",
        "mold": "模具",
        "die": "模具",
        "pattern": "模型",
        "template": "样板",

        # Adjectives / modifiers
        "hydraulic": "液压",
        "pneumatic": "气动",
        "electric": "电动",
        "mechanical": "机械",
        "automatic": "自动",
        "manual": "手动",
        "digital": "数字",
        "analog": "模拟",
        "high": "高",
        "low": "低",
        "large": "大",
        "small": "小",
        "fast": "快速",
        "slow": "慢速",
        "heavy": "重型",
        "light": "轻型",
        "standard": "标准",
        "special": "特殊",
        "general": "通用",
        "precision": "精密",
        "rough": "粗",
        "fine": "精",

        # Industry
        "industrial": "工业",
        "manufacturing": "制造",
        "production": "生产",
        "automotive": "汽车",
        "aerospace": "航空航天",
        "marine": "船舶",
        "railway": "铁路",
        "construction": "建筑",
        "mining": "采矿",
        "agricultural": "农业",
        "nuclear": "核",
        "chemical": "化学",
        "petroleum": "石油",

        # Verbs
        "design": "设计",
        "analysis": "分析",
        "control": "控制",
        "monitor": "监测",
        "protect": "防护",
        "prevent": "预防",
        "reduce": "减少",
        "increase": "增加",
        "measure": "测量",
        "calculate": "计算",
        "optimize": "优化",
        "improve": "改进",
        "maintain": "维护",
        "repair": "修理",
        "install": "安装",
        "remove": "拆卸",
        "replace": "更换",
        "adjust": "调整",
    })

    # 6. Category-specific suffix rules
    pattern_rules = [
        # X steel → X钢
        (r'^(.+)\s+steel$', r'\1钢'),
        (r'^(.+)\s+iron$', r'\1铁'),
        # X bearing → X轴承
        (r'^(.+)\s+bearing$', r'\1轴承'),
        # X gear → X齿轮
        (r'^(.+)\s+gear$', r'\1齿轮'),
        # X valve → X阀
        (r'^(.+)\s+valve$', r'\1阀'),
        # X pump → X泵
        (r'^(.+)\s+pump$', r'\1泵'),
        # X joint → X接头
        (r'^(.+)\s+joint$', r'\1接头'),
        # X seal → X密封
        (r'^(.+)\s+seal$', r'\1密封'),
        # X spring → X弹簧
        (r'^(.+)\s+spring$', r'\1弹簧'),
        # X screw → X螺钉
        (r'^(.+)\s+screw$', r'\1螺钉'),
        # X bolt → X螺栓
        (r'^(.+)\s+bolt$', r'\1螺栓'),
        # X nut → X螺母
        (r'^(.+)\s+nut$', r'\1螺母'),
        # X washer → X垫圈
        (r'^(.+)\s+washer$', r'\1垫圈'),
        # X pin → X销
        (r'^(.+)\s+pin$', r'\1销'),
        # X coupling → X联轴器
        (r'^(.+)\s+coupling$', r'\1联轴器'),
        # X clutch → X离合器
        (r'^(.+)\s+clutch$', r'\1离合器'),
        # X brake → X制动器
        (r'^(.+)\s+brake$', r'\1制动器'),
        # X belt → X带
        (r'^(.+)\s+belt$', r'\1带'),
        # X chain → X链
        (r'^(.+)\s+chain$', r'\1链'),
        # X engine → X发动机
        (r'^(.+)\s+engine$', r'\1发动机'),
        # X motor → X电动机
        (r'^(.+)\s+motor$', r'\1电动机'),
        # X cylinder → X缸
        (r'^(.+)\s+cylinder$', r'\1缸'),
        # X piston → X活塞
        (r'^(.+)\s+piston$', r'\1活塞'),
        # X pipe → X管
        (r'^(.+)\s+pipe$', r'\1管'),
        # X tube → X管
        (r'^(.+)\s+tube$', r'\1管'),
        # X plate → X板
        (r'^(.+)\s+plate$', r'\1板'),
        # X rod → X杆
        (r'^(.+)\s+rod$', r'\1杆'),
        # X shaft → X轴
        (r'^(.+)\s+shaft$', r'\1轴'),
        # X ring → X环
        (r'^(.+)\s+ring$', r'\1环'),
        # X flange → X法兰
        (r'^(.+)\s+flange$', r'\1法兰'),
        # X gasket → X垫片
        (r'^(.+)\s+gasket$', r'\1垫片'),
        # X bushing → X衬套
        (r'^(.+)\s+bushing$', r'\1衬套'),
        # X sensor → X传感器
        (r'^(.+)\s+sensor$', r'\1传感器'),
        # X meter → X表/计
        (r'^(.+)\s+meter$', r'\1表'),
        # X machine → X机
        (r'^(.+)\s+machine$', r'\1机'),
        # X press → X压力机
        (r'^(.+)\s+press$', r'\1压力机'),
        # X furnace → X炉
        (r'^(.+)\s+furnace$', r'\1炉'),
        # X test → X试验
        (r'^(.+)\s+test$', r'\1试验'),
        # X oil → X油
        (r'^(.+)\s+oil$', r'\1油'),
        # X resistance → X阻力/电阻
        (r'^(.+)\s+resistance$', r'\1阻力'),
        # X ratio → X比
        (r'^(.+)\s+ratio$', r'\1比'),
        # X force → X力
        (r'^(.+)\s+force$', r'\1力'),
        # X stress → X应力
        (r'^(.+)\s+stress$', r'\1应力'),
        # X strength → X强度
        (r'^(.+)\s+strength$', r'\1强度'),
        # X hardness → X硬度
        (r'^(.+)\s+hardness$', r'\1硬度'),
        # X toughness → X韧性
        (r'^(.+)\s+toughness$', r'\1韧性'),
        # X pressure → X压力
        (r'^(.+)\s+pressure$', r'\1压力'),
        # X temperature → X温度
        (r'^(.+)\s+temperature$', r'\1温度'),
        # X velocity → X速度
        (r'^(.+)\s+velocity$', r'\1速度'),
        # X rate → X率
        (r'^(.+)\s+rate$', r'\1率'),
        # X depth → X深度
        (r'^(.+)\s+depth$', r'\1深度'),
        # X width → X宽度
        (r'^(.+)\s+width$', r'\1宽度'),
        # X length → X长度
        (r'^(.+)\s+length$', r'\1长度'),
        # X diameter → X直径
        (r'^(.+)\s+diameter$', r'\1直径'),
        # X angle → X角
        (r'^(.+)\s+angle$', r'\1角'),
        # X system → X系统
        (r'^(.+)\s+system$', r'\1系统'),
        # X process → X工艺
        (r'^(.+)\s+process$', r'\1工艺'),
        # X method → X法
        (r'^(.+)\s+method$', r'\1法'),
        # X principle → X原理
        (r'^(.+)\s+principle$', r'\1原理'),
        # X law → X定律
        (r'^(.+)\s+law$', r'\1定律'),
        # X theory → X理论
        (r'^(.+)\s+theory$', r'\1理论'),
        # X equation → X方程
        (r'^(.+)\s+equation$', r'\1方程'),
        # X formula → X公式
        (r'^(.+)\s+formula$', r'\1公式'),
        # X number → X数
        (r'^(.+)\s+number$', r'\1数'),
        # X coefficient → X系数
        (r'^(.+)\s+coefficient$', r'\1系数'),
        # X efficiency → X效率
        (r'^(.+)\s+efficiency$', r'\1效率'),
        # X capacity → X容量
        (r'^(.+)\s+capacity$', r'\1容量'),
        # X speed → X速度
        (r'^(.+)\s+speed$', r'\1速度'),
        # X type → X型
        (r'^(.+)\s+type$', r'\1型'),
        # X grade → X级
        (r'^(.+)\s+grade$', r'\1级'),
        # X class → X级
        (r'^(.+)\s+class$', r'\1级'),
        # X coating → X涂层
        (r'^(.+)\s+coating$', r'\1涂层'),
        # X alloy → X合金
        (r'^(.+)\s+alloy$', r'\1合金'),
        # X welding → X焊
        (r'^(.+)\s+welding$', r'\1焊'),
        # X casting → X铸造
        (r'^(.+)\s+casting$', r'\1铸造'),
        # X forging → X锻造
        (r'^(.+)\s+forging$', r'\1锻造'),
        # X machining → X加工
        (r'^(.+)\s+machining$', r'\1加工'),
        # X cutting → X切削
        (r'^(.+)\s+cutting$', r'\1切削'),
        # X forming → X成形
        (r'^(.+)\s+forming$', r'\1成形'),
        # X treatment → X处理
        (r'^(.+)\s+treatment$', r'\1处理'),
        # X analysis → X分析
        (r'^(.+)\s+analysis$', r'\1分析'),
        # X measurement → X测量
        (r'^(.+)\s+measurement$', r'\1测量'),
        # X inspection → X检验
        (r'^(.+)\s+inspection$', r'\1检验'),
        # X control → X控制
        (r'^(.+)\s+control$', r'\1控制'),
        # X technique → X技术
        (r'^(.+)\s+technique$', r'\1技术'),
        # X technology → X技术
        (r'^(.+)\s+technology$', r'\1技术'),
        # X engineering → X工程
        (r'^(.+)\s+engineering$', r'\1工程'),
        # X science → X科学
        (r'^(.+)\s+science$', r'\1科学'),
    ]

    return term_dict, word_dict, pattern_rules


def _guess_word_translation(word, zh_phrase, words):
    """Guess the translation of a single word from a multi-word phrase translation"""
    idx = words.index(word)
    if idx == 0:
        # First word — might map to first part of zh
        for known_zh in [w for w in word_dict.values()]:
            if zh_phrase.startswith(known_zh) and len(known_zh) <= len(zh_phrase) // 2:
                return known_zh
    return None


def compose_translation(en_term, term_dict, word_dict, pattern_rules):
    """Attempt to compose a Chinese translation for an English term

    Strategy:
    1. Check exact match in term_dict
    2. Check sub-term match (term contains a known term)
    3. Apply pattern rules (X steel → X钢)
    4. Word-by-word composition
    5. Return None if all fail
    """
    en_lower = en_term.strip().lower()

    # 1. Exact match
    if en_lower in term_dict:
        return term_dict[en_lower]

    # 2. Sub-term match — check if en_term contains a known sub-term
    for known_en, known_zh in sorted(term_dict.items(), key=lambda x: -len(x[0])):
        if known_en in en_lower and known_en != en_lower:
            return known_zh

    # 3. Pattern rules
    for pattern, template in pattern_rules:
        m = re.match(pattern, en_lower, re.IGNORECASE)
        if m:
            prefix = m.group(1)
            # Try to translate prefix
            prefix_zh = compose_translation(prefix, term_dict, word_dict, pattern_rules)
            if prefix_zh:
                result = template.replace(r'\1', prefix_zh)
                return result

    # 4. Word-by-word composition
    words = en_lower.split()
    if len(words) >= 2:
        zh_parts = []
        all_found = True
        for w in words:
            if w in word_dict:
                zh_parts.append(word_dict[w])
            else:
                all_found = False
                break
        if all_found and zh_parts:
            return ''.join(zh_parts)

    # 5. Try single-word direct mapping for non-compound terms
    words = en_lower.replace('-', ' ').replace('_', ' ').split()
    if len(words) == 1 and words[0] in word_dict:
        return word_dict[words[0]]

    return None


def phase_e1_apply_corrections(v4_data):
    """Phase E1: Apply 30 canonical corrections to mech-terminology-v4.json"""
    corrections_applied = 0
    for t in v4_data.get("terms", []):
        en = t.get("en", "").strip().lower()
        if en in E1_CORRECTIONS or t.get("en", "").strip() in E1_CORRECTIONS:
            en_orig = t.get("en", "").strip()
            if en_orig in E1_CORRECTIONS:
                correct_zh = E1_CORRECTIONS[en_orig]
            else:
                correct_zh = E1_CORRECTIONS[en]
            old_zh = t.get("zh", "")
            t["zh"] = correct_zh
            t["source"] = t.get("source", "") + "+e1"
            corrections_applied += 1
            print(f"  E1: {en_orig:45s} '{old_zh:20s}' → '{correct_zh}'")
    return v4_data, corrections_applied


def phase_e2_generate_translations(v4_data, term_dict, word_dict, pattern_rules):
    """Phase E2: Generate translations for untranslated and partial terms"""
    stats = {"exact_match": 0, "subterm_match": 0, "word_compose": 0,
             "pattern_match": 0, "failed": 0, "skipped_good": 0}
    generated = []

    for t in v4_data.get("terms", []):
        en = t.get("en", "").strip()
        zh = t.get("zh", "").strip()
        src = t.get("source", "")

        # Check if this term needs translation
        # Skip if already has good zh
        if zh and len(zh) >= 2:
            has_ascii = any(c.isascii() and c.isalpha() for c in zh)
            if not has_ascii:
                stats["skipped_good"] += 1
                continue

        # Generate translation
        result = compose_translation(en, term_dict, word_dict, pattern_rules)
        if result:
            t["zh"] = result
            t["source"] = src + "+e2"
            generated.append((en, result))
            # Determine which method worked (for stats)
            en_lower = en.strip().lower()
            if en_lower in term_dict:
                stats["exact_match"] += 1
            elif any(k in en_lower and k != en_lower for k in term_dict):
                stats["subterm_match"] += 1
            else:
                # Figure out if it was pattern or composition
                words = en_lower.split()
                if len(words) >= 2:
                    stats["word_compose"] += 1
                else:
                    stats["pattern_match"] += 1
        else:
            stats["failed"] += 1

    return v4_data, stats, generated


def phase_e2_process_extras(v4_data, term_dict, word_dict, pattern_rules):
    """Also attempt to fix extracted_extras translations"""
    stats = {"fixed": 0, "already_good": 0, "failed": 0}
    for e in v4_data.get("extracted_extras", []):
        zh = e.get("zh", "").strip()
        en = e.get("en", "").strip()

        if not zh:
            result = compose_translation(en, term_dict, word_dict, pattern_rules)
            if result:
                e["zh"] = result
                e["source"] = e.get("source", "") + "+e2"
                stats["fixed"] += 1
            else:
                e["zh"] = f"[需翻译]{en}"
                stats["failed"] += 1
            continue

        has_ascii = any(c.isascii() and c.isalpha() for c in zh)
        zh_only_en = zh.lower().strip() == en.lower().strip()
        if has_ascii or zh_only_en or len(zh) < 2:
            result = compose_translation(en, term_dict, word_dict, pattern_rules)
            if result:
                e["zh"] = result
                e["source"] = e.get("source", "") + "+e2"
                stats["fixed"] += 1
            else:
                e["zh"] = f"[需翻译]{en}"
                stats["failed"] += 1
        else:
            stats["already_good"] += 1

    return v4_data, stats


def main():
    print("=" * 60)
    print("Phase E1+E2: 术语翻译批量修正与自动补齐")
    print("=" * 60)

    # Load data
    v4 = load_json(KB / "mech-terminology-v4.json")
    if not v4:
        print("ERROR: mech-terminology-v4.json not found", file=sys.stderr)
        sys.exit(1)

    terms_before = len(v4.get("terms", []))
    extras_before = len(v4.get("extracted_extras", []))
    print(f"\n加载 v4 数据: {terms_before} terms, {extras_before} extras")

    # Phase E1
    print("\n── Phase E1: 批量修正 30 条术语偏差 ──")
    v4, e1_count = phase_e1_apply_corrections(v4)
    print(f"  → 已修正 {e1_count} 条")

    # Build translation engine
    term_dict, word_dict, pattern_rules = build_translation_engine()
    print(f"\n翻译引擎: {len(term_dict)} 条精确匹配, {len(word_dict)} 个词级映射, {len(pattern_rules)} 条模式规则")

    # Phase E2: terms
    print("\n── Phase E2: 自动补齐术语翻译 ──")
    print("  处理 terms...")
    v4, e2_stats, generated = phase_e2_generate_translations(v4, term_dict, word_dict, pattern_rules)

    print(f"  ✓ 精确匹配: {e2_stats['exact_match']}")
    print(f"  ✓ 子术语匹配: {e2_stats['subterm_match']}")
    print(f"  ✓ 词级组合: {e2_stats['word_compose']}")
    print(f"  ✓ 模式规则: {e2_stats['pattern_match']}")
    print(f"  ✗ 失败(需人工): {e2_stats['failed']}")
    print(f"  - 原已正确: {e2_stats['skipped_good']}")
    total_generated = e2_stats['exact_match'] + e2_stats['subterm_match'] + e2_stats['word_compose'] + e2_stats['pattern_match']
    print(f"  → 共生成 {total_generated} 条翻译")

    # Phase E2: extras
    print("\n  处理 extracted_extras...")
    v4, ex_stats = phase_e2_process_extras(v4, term_dict, word_dict, pattern_rules)
    print(f"  ✓ 已修复: {ex_stats['fixed']}")
    print(f"  ✓ 原已正确: {ex_stats['already_good']}")
    print(f"  ✗ 失败(需人工): {ex_stats['failed']}")

    # Save v5
    v4["meta"]["version"] = "5"
    v4["meta"]["generated"] = "2026-05-19"
    v4["meta"]["phase_e1"] = e1_count
    v4["meta"]["phase_e2_terms"] = total_generated
    v4["meta"]["phase_e2_extras"] = ex_stats['fixed']
    v4["meta"]["phase_e2_failed"] = e2_stats['failed']
    v4["meta"]["phase_e2_extras_failed"] = ex_stats['failed']
    v4["meta"]["total_terms_v5"] = len(v4.get("terms", []))
    v4["meta"]["total_extras_v5"] = len(v4.get("extracted_extras", []))

    v5_path = KB / "mech-terminology-v5.json"
    v5_path.write_text(json.dumps(v4, ensure_ascii=False, indent=2))
    print(f"\n✅ 已保存 v5: {v5_path}")

    # Save failed terms list for manual translation
    failed_terms = [t for t in v4.get("terms", [])
                    if any(c.isascii() and c.isalpha() for c in t.get("zh", ""))
                    or t.get("zh", "").lower() == t.get("en", "").lower()
                    or not t.get("zh", "")]
    failed_extras = [e for e in v4.get("extracted_extras", [])
                     if any(c.isascii() and c.isalpha() for c in e.get("zh", ""))
                     or e.get("zh", "").startswith("[需翻译]")]

    print(f"\n  需人工翻译: {len(failed_terms)} terms + {len(failed_extras)} extras")

    # Summary
    terms_after = len(v4.get("terms", []))
    extras_after = len(v4.get("extracted_extras", []))
    good_terms = sum(1 for t in v4.get("terms", [])
                     if len(t.get("zh", "")) >= 2
                     and not any(c.isascii() and c.isalpha() for c in t.get("zh", ""))
                     and t.get("zh", "").lower() != t.get("en", "").lower())
    good_extras = sum(1 for e in v4.get("extracted_extras", [])
                      if len(e.get("zh", "")) >= 2
                      and not any(c.isascii() and c.isalpha() for c in e.get("zh", "")))

    print(f"\n{'='*60}")
    print(f"最终统计")
    print(f"{'='*60}")
    print(f"  v4 → v5: {terms_before} terms → {terms_after} terms")
    print(f"  v4 → v5: {extras_before} extras → {extras_after} extras")
    print(f"  质量合格的术语翻译: {good_terms}/{terms_after}")
    print(f"  质量合格的额外翻译: {good_extras}/{extras_after}")

    return v4, v5_path


if __name__ == "__main__":
    main()
