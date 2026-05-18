#!/usr/bin/env python3
"""
B11: 机械工程术语表V3扩展至5000+条
从所有数据源提取术语，生成中英对照+定义
无LLM依赖，纯Python规则引擎
"""
import json, re, sys
from pathlib import Path
from collections import Counter

BASE = Path(__file__).parent.parent
KB = BASE / "knowledge-base"
RAW = BASE / "raw"
OUTPUT_JSON = KB / "mech-terminology-v3.json"
OUTPUT_MD = KB / "mech-terminology-v3.md"

def load_json(path):
    try:
        data = json.loads(path.read_text())
        return data if data else []
    except: return []

def load_existing_terms():
    """Load existing terminology v2 as base"""
    path = KB / "mech-terminology-v2.json"
    if not path.exists(): return {}, {}
    data = json.loads(path.read_text())
    terms = {}
    for t in data.get("terms", []):
        key = t["en"].strip().lower()
        terms[key] = t
    extras = {}
    for t in data.get("extracted_extras", []):
        key = t["en"].strip().lower()
        extras[key] = t
    return terms, extras

# ---- 中英翻译字典（自动生成新术语的中文翻译） ----
# 600+ 核心翻译对，涵盖机械工程所有领域
TRANSLATION_DICT = {
    # A
    "abrasive": "磨料", "abrasion": "磨耗", "absorber": "吸收器", "absorption": "吸收",
    "accelerometer": "加速度计", "accumulator": "蓄能器", "accuracy": "精度",
    "actuator": "执行器", "adapter": "适配器", "addendum": "齿顶高",
    "adhesive": "粘合剂", "adjustment": "调整", "advance": "进给",
    "aerodynamics": "空气动力学", "agitator": "搅拌器", "allowance": "允差",
    "alumina": "氧化铝", "aluminum": "铝", "amplifier": "放大器",
    "amplitude": "振幅", "analysis": "分析", "anchor": "锚固件",
    "angle": "角度", "angular": "角度的", "anisotropy": "各向异性",
    "annealing": "退火", "anodizing": "阳极氧化", "aperture": "孔径",
    "apparatus": "装置", "applicator": "涂布器", "arbor": "心轴",
    "arc": "电弧", "architecture": "架构", "arm": "臂",
    "arrangement": "布置", "articulation": "铰接", "asbestos": "石棉",
    "assembly": "装配", "atmosphere": "气氛", "attenuator": "衰减器",
    "austenite": "奥氏体", "autocad": "AutoCAD", "automation": "自动化",
    "auxiliary": "辅助的", "axial": "轴向的", "axis": "轴线",
    "axle": "车轴",
    # B
    "backlash": "齿隙", "baffle": "挡板", "balance": "平衡",
    "ball": "球", "ballast": "镇流器", "band": "带",
    "bar": "杆", "barrel": "筒体", "base": "底座",
    "batten": "压条", "beam": "梁", "bearing": "轴承",
    "bed": "床身", "bell": "钟形", "belt": "带",
    "bench": "工作台", "bend": "弯曲", "bevel": "斜面",
    "billet": "坯料", "binder": "粘结剂", "blade": "叶片",
    "blank": "毛坯", "blast": "喷砂", "bleed": "放气",
    "block": "块", "blower": "鼓风机", "board": "板",
    "body": "本体", "boiler": "锅炉", "bolt": "螺栓",
    "bond": "结合", "bore": "孔", "boring": "镗削",
    "boss": "凸台", "bottleneck": "瓶颈", "bottom": "底部",
    "bracket": "支架", "brake": "制动器", "branch": "支管",
    "brass": "黄铜", "brazing": "钎焊", "break": "断裂",
    "bridge": "桥架", "brinell": "布氏硬度", "broaching": "拉削",
    "bronze": "青铜", "brush": "电刷", "buckle": "屈曲",
    "buffer": "缓冲器", "bulkhead": "隔板", "bushing": "衬套",
    "butterfly": "蝶形", "button": "按钮",
    # C
    "cabinet": "机柜", "cable": "电缆", "cadmium": "镉",
    "cage": "保持架", "calibration": "校准", "cam": "凸轮",
    "cantilever": "悬臂梁", "cap": "盖", "capacitor": "电容器",
    "capacity": "容量", "capillary": "毛细管", "carbide": "硬质合金",
    "carbon": "碳", "carburizing": "渗碳", "carrier": "承载件",
    "cartridge": "筒", "cascade": "级联", "case": "壳体",
    "casing": "外壳", "cast": "铸造", "catalyst": "催化剂",
    "cavitation": "空化", "cell": "单元", "cement": "水泥",
    "center": "中心", "centrifuge": "离心机", "ceramic": "陶瓷",
    "certification": "认证", "chain": "链条", "chamber": "腔室",
    "chamfer": "倒角", "channel": "通道", "characteristic": "特性",
    "charge": "充电", "chassis": "底盘", "check": "检查",
    "chiller": "冷却器", "chip": "切屑", "chuck": "卡盘",
    "circle": "圆", "circuit": "电路", "circular": "圆形的",
    "clad": "包覆", "clamp": "夹紧", "class": "等级",
    "clearance": "间隙", "clutch": "离合器", "coating": "涂层",
    "coefficient": "系数", "coil": "线圈", "cold": "冷",
    "collector": "收集器", "column": "立柱", "combustion": "燃烧",
    "compensator": "补偿器", "component": "元件", "composite": "复合材料",
    "compound": "复合", "compression": "压缩", "compressor": "压缩机",
    "concentrator": "浓缩器", "concentricity": "同轴度", "condenser": "冷凝器",
    "conditioner": "调节器", "conduction": "传导", "conductor": "导体",
    "conduit": "导管", "cone": "锥体", "connection": "连接",
    "connector": "连接器", "console": "控制台", "constant": "常数",
    "constraint": "约束", "construction": "结构", "contact": "接触",
    "container": "容器", "control": "控制", "controller": "控制器",
    "convection": "对流", "convergence": "收敛", "converter": "转换器",
    "conveyor": "输送机", "coolant": "冷却液", "cooler": "冷却器",
    "cooling": "冷却", "core": "型芯", "corrosion": "腐蚀",
    "counter": "计数器", "coupling": "联轴器", "cover": "盖板",
    "crack": "裂纹", "cradle": "支架", "crane": "起重机",
    "crank": "曲柄", "crankshaft": "曲轴", "creep": "蠕变",
    "crosshead": "十字头", "crystal": "晶体", "cure": "固化",
    "current": "电流", "curvature": "曲率", "cushion": "缓冲垫",
    "cut": "切削", "cutter": "刀具", "cutting": "切削",
    "cycle": "循环", "cylinder": "气缸", "cylindrical": "圆柱的",
    # D
    "damper": "阻尼器", "dashpot": "缓冲器", "datum": "基准",
    "dead": "死", "debris": "碎屑", "decay": "衰减",
    "deceleration": "减速", "deck": "甲板", "deflection": "挠度",
    "deformation": "变形", "degreaser": "脱脂剂", "delivery": "输送",
    "density": "密度", "deposit": "沉积", "derrick": "井架",
    "design": "设计", "detector": "检测器", "device": "装置",
    "diagnostic": "诊断", "diaphragm": "隔膜", "die": "模具",
    "diesel": "柴油机", "diffuser": "扩压器", "diffusion": "扩散",
    "dilatometer": "膨胀计", "dimension": "尺寸", "diode": "二极管",
    "discharge": "排放", "displacement": "位移", "dissipation": "耗散",
    "distillation": "蒸馏", "distribution": "分配", "distributor": "分配器",
    "diverter": "换向器", "dome": "穹顶", "door": "门",
    "dosing": "计量", "dowel": "定位销", "draft": "通风",
    "drag": "阻力", "drain": "排水", "draw": "拉延",
    "drawing": "图纸", "drill": "钻头", "drilling": "钻孔",
    "drive": "驱动", "driver": "驱动器", "drum": "滚筒",
    "dryer": "干燥器", "duct": "管道", "ductility": "延展性",
    "dummy": "假件", "dump": "卸料", "duplex": "双重的",
    "durability": "耐久性", "dwell": "停留", "dynamics": "动力学",
    "dynamometer": "测功机",
    # E
    "eccentric": "偏心", "efficiency": "效率", "ejector": "顶出器",
    "elasticity": "弹性", "elbow": "弯头", "electric": "电的",
    "electrode": "电极", "electrolysis": "电解", "electromagnet": "电磁铁",
    "electronics": "电子学", "element": "元素", "elevator": "升降机",
    "eliminator": "消除器", "elongation": "伸长率", "embossing": "压花",
    "emission": "排放", "enclosure": "外壳", "encoder": "编码器",
    "energy": "能量", "engine": "发动机", "engineering": "工程",
    "enthalpy": "焓", "entropy": "熵", "envelope": "包络",
    "epicyclic": "周转轮系", "equalizer": "平衡器", "equation": "方程",
    "equipment": "设备", "erector": "安装器", "ergonomics": "人机工程学",
    "erosion": "冲蚀", "error": "误差", "evacuation": "抽空",
    "evaporator": "蒸发器", "examination": "检查", "excavator": "挖掘机",
    "exchanger": "交换器", "exhaust": "排气", "expansion": "膨胀",
    "experiment": "实验", "explosion": "爆炸", "extensometer": "引伸计",
    "extinguisher": "灭火器", "extraction": "提取", "extruder": "挤出机",
    "extrusion": "挤压", "eye": "眼环",
    # F
    "fabric": "织物", "fabrication": "制造", "face": "面",
    "factor": "因子", "failure": "失效", "fan": "风扇",
    "fastener": "紧固件", "fatigue": "疲劳", "feeder": "给料机",
    "ferrite": "铁素体", "fiber": "纤维", "filament": "灯丝",
    "file": "锉刀", "filler": "填充物", "film": "膜",
    "filter": "过滤器", "filtration": "过滤", "fin": "翅片",
    "finished": "精加工的", "finite": "有限", "fitting": "管件",
    "fixture": "夹具", "flame": "火焰", "flange": "法兰",
    "flash": "飞边", "flatness": "平面度", "flexibility": "柔性",
    "flexure": "挠曲", "float": "浮子", "floor": "地板",
    "flow": "流动", "flue": "烟道", "fluid": "流体",
    "fluorocarbon": "氟碳", "flush": "冲洗", "flux": "通量",
    "flywheel": "飞轮", "foam": "泡沫", "follower": "从动件",
    "foot": "底座", "force": "力", "forge": "锻造",
    "fork": "叉", "form": "形状", "forming": "成型",
    "formula": "公式", "foundation": "基础", "foundry": "铸造厂",
    "fracture": "断裂", "frame": "机架", "frequency": "频率",
    "friction": "摩擦", "furnace": "炉", "fuse": "熔断器",
    # G
    "gage": "量规", "gantry": "龙门架", "gap": "间隙",
    "gasket": "垫片", "gas": "气体", "gate": "浇口",
    "gauge": "仪表", "gear": "齿轮", "generator": "发电机",
    "gib": "镶条", "gland": "压盖", "glass": "玻璃",
    "globe": "球阀", "governor": "调速器", "grade": "等级",
    "gradient": "梯度", "grain": "晶粒", "granulator": "造粒机",
    "graphite": "石墨", "gravity": "重力", "grease": "润滑脂",
    "grid": "网格", "grinder": "磨床", "grinding": "磨削",
    "gripper": "夹爪", "groove": "沟槽", "guard": "防护罩",
    "guide": "导轨", "gusset": "角撑板", "gyroscope": "陀螺仪",
    # H
    "hammer": "锤", "hand": "手", "handle": "手柄",
    "hanger": "吊架", "hardening": "硬化", "hardness": "硬度",
    "harmonic": "谐波", "head": "头部", "header": "集管",
    "heat": "热", "heater": "加热器", "heating": "加热",
    "helix": "螺旋", "hinge": "铰链", "hob": "滚刀",
    "holder": "夹持器", "hole": "孔", "honing": "珩磨",
    "hood": "罩", "hook": "钩", "hopper": "料斗",
    "horn": "喇叭", "hose": "软管", "housing": "壳体",
    "hub": "轮毂", "humidity": "湿度", "hydraulics": "液压",
    "hydrostatic": "静压",
    # I
    "ignition": "点火", "impeller": "叶轮", "implant": "植入物",
    "impulse": "脉冲", "incline": "倾斜", "indentation": "压痕",
    "index": "索引", "indicator": "指示器", "induction": "感应",
    "injector": "喷射器", "inlet": "入口", "insert": "嵌件",
    "inspection": "检验", "instrument": "仪器", "insulation": "绝缘",
    "intake": "进气", "interface": "接口", "interlock": "互锁",
    "inverter": "逆变器", "ion": "离子", "iron": "铁",
    "irrigation": "灌溉", "isolation": "隔离", "isotropy": "各向同性",
    # J
    "jack": "千斤顶", "jacket": "夹套", "jaw": "颚板",
    "jet": "喷射", "jig": "夹具", "joint": "接头",
    "journal": "轴颈",
    # K
    "key": "键", "keyseat": "键槽", "keyway": "键槽",
    "knee": "膝", "knob": "旋钮", "knuckle": "关节",
    # L
    "label": "标签", "laboratory": "实验室", "labyrinth": "迷宫",
    "lacquer": "漆", "lagging": "保温层", "laminate": "层压",
    "lamp": "灯", "laser": "激光", "lathe": "车床",
    "lattice": "晶格", "layer": "层", "layout": "布局",
    "lead": "导程", "leader": "引线", "leaf": "叶片",
    "leak": "泄漏", "leg": "腿", "length": "长度",
    "level": "水平", "lever": "杠杆", "lift": "提升",
    "ligament": "韧带", "limit": "极限", "line": "线",
    "linear": "线性的", "liner": "衬里", "link": "连杆",
    "linkage": "连杆机构", "liquid": "液体", "load": "载荷",
    "lock": "锁", "locomotive": "机车", "lubricant": "润滑剂",
    "lubrication": "润滑",
    # M
    "machine": "机器", "machinery": "机械", "machining": "机械加工",
    "magnesium": "镁", "magnet": "磁铁", "malleability": "可锻性",
    "manifold": "歧管", "manometer": "压力计", "manufacturing": "制造",
    "marking": "标记", "mast": "桅杆", "master": "主",
    "material": "材料", "matrix": "基体", "mechanism": "机构",
    "mechatronics": "机电一体化", "melt": "熔体", "membrane": "膜",
    "mesh": "网格", "metal": "金属", "meter": "仪表",
    "method": "方法", "microprocessor": "微处理器", "microscope": "显微镜",
    "milling": "铣削", "mixer": "混合器", "mixture": "混合物",
    "model": "模型", "modulus": "模量", "moisture": "水分",
    "mold": "模具", "molecule": "分子", "moment": "力矩",
    "monitor": "监控器", "motor": "电机", "mount": "安装座",
    "muffler": "消声器",
    # N
    "nanometer": "纳米", "neck": "颈部", "needle": "针",
    "network": "网络", "neutral": "中性的", "nickel": "镍",
    "nipple": "螺纹接头", "nitriding": "渗氮", "node": "节点",
    "noise": "噪声", "nozzle": "喷嘴", "nut": "螺母",
    # O
    "offset": "偏置", "oil": "油", "operator": "操作员",
    "optic": "光学", "orifice": "孔口", "oscillation": "振荡",
    "oven": "烘箱", "overflow": "溢流", "overhaul": "大修",
    "oxide": "氧化物",
    # P
    "packing": "填料", "pad": "垫", "paint": "涂料",
    "panel": "面板", "parallel": "平行", "parameter": "参数",
    "part": "零件", "pawl": "棘爪", "peak": "峰值",
    "pedestal": "支座", "peen": "喷丸", "pendulum": "摆",
    "penetration": "穿透", "performance": "性能", "perimeter": "周长",
    "permit": "许可", "pipeline": "管道", "piston": "活塞",
    "pitch": "螺距", "pivot": "枢轴", "plain": "普通的",
    "plan": "计划", "plane": "平面", "plasma": "等离子体",
    "plastic": "塑料", "plasticity": "塑性", "plate": "板",
    "platform": "平台", "plating": "电镀", "plenum": "压力腔",
    "pliers": "钳子", "plug": "插头", "plunger": "柱塞",
    "ply": "层", "pneumatic": "气动", "pointer": "指针",
    "polarity": "极性", "polish": "抛光", "pollution": "污染",
    "polymer": "聚合物", "port": "端口", "position": "位置",
    "positioner": "定位器", "pot": "罐", "powder": "粉末",
    "power": "功率", "precision": "精度", "preheater": "预热器",
    "press": "压力机", "pressure": "压力", "prestressing": "预应力",
    "probe": "探头", "process": "工艺", "processor": "处理器",
    "profile": "轮廓", "propeller": "螺旋桨", "property": "性能",
    "proportion": "比例", "protection": "保护", "prototype": "原型",
    "pulley": "带轮", "pulse": "脉冲", "pump": "泵",
    "punch": "冲头", "purification": "净化", "push": "推",
    "pyrometer": "高温计",
    # Q
    "qualification": "鉴定", "quality": "质量", "quenching": "淬火",
    # R
    "rack": "齿条", "radar": "雷达", "radial": "径向的",
    "radiator": "散热器", "ram": "滑块", "ratio": "比率",
    "reactor": "反应器", "reamer": "铰刀", "reaming": "铰孔",
    "recorder": "记录仪", "reducer": "减速器", "refinery": "精炼厂",
    "reflector": "反射器", "refrigerant": "制冷剂", "regulator": "调节器",
    "reinforcement": "增强", "relay": "继电器", "release": "释放",
    "relief": "卸荷", "reservoir": "储液器", "resistance": "阻力",
    "resolver": "旋转变压器", "resonance": "共振", "retainer": "保持架",
    "retort": "蒸馏罐", "revolution": "旋转", "rheostat": "变阻器",
    "rib": "筋", "rig": "钻机", "rigidity": "刚性",
    "rim": "轮辋", "ring": "环", "ripple": "纹波",
    "riser": "冒口", "rivet": "铆钉", "robot": "机器人",
    "robotics": "机器人学", "rod": "杆", "roll": "轧辊",
    "roller": "滚子", "roof": "顶部", "root": "根部",
    "rope": "绳索", "rotameter": "转子流量计", "rotary": "旋转的",
    "rotor": "转子", "roughness": "粗糙度", "roundness": "圆度",
    "rubber": "橡胶", "runner": "流道", "rust": "锈",
    # S
    "saddle": "鞍座", "safety": "安全", "sag": "垂度",
    "sample": "样品", "sand": "砂", "saw": "锯",
    "scaffold": "脚手架", "scale": "比例", "scanner": "扫描仪",
    "scraper": "刮刀", "screen": "筛网", "screw": "螺钉",
    "seal": "密封", "seat": "座", "section": "截面",
    "segment": "段", "selector": "选择器", "sensor": "传感器",
    "separator": "分离器", "servo": "伺服", "shaft": "轴",
    "shaker": "振动器", "shear": "剪切", "sheet": "板材",
    "shell": "壳体", "shield": "屏蔽", "shock": "冲击",
    "shoe": "制动蹄", "shroud": "屏蔽罩", "shutoff": "切断",
    "shuttle": "梭", "sieve": "筛", "sight": "观察",
    "signal": "信号", "silencer": "消声器", "silicone": "硅酮",
    "sintering": "烧结", "siphon": "虹吸", "sizing": "定径",
    "sleeve": "套筒", "slide": "滑板", "slider": "滑块",
    "slip": "滑动", "slot": "槽", "smoothing": "平滑",
    "socket": "插座", "solenoid": "电磁阀", "solid": "固体",
    "sorter": "分拣机", "spacer": "隔套", "spanner": "扳手",
    "spatial": "空间的", "specification": "规格", "spectrum": "光谱",
    "speed": "速度", "spindle": "主轴", "spiral": "螺旋",
    "spline": "花键", "split": "剖分", "spool": "阀芯",
    "spring": "弹簧", "sprocket": "链轮", "stability": "稳定性",
    "stabilizer": "稳定器", "stack": "烟囱", "stainless": "不锈钢",
    "stamping": "冲压", "standard": "标准", "standby": "备用",
    "starter": "启动器", "statics": "静力学", "stator": "定子",
    "steam": "蒸汽", "steel": "钢", "stepper": "步进",
    "stiffener": "加强筋", "stiffness": "刚度", "stirrer": "搅拌器",
    "stock": "毛坯", "stop": "止动", "storage": "存储",
    "strain": "应变", "strap": "带", "strength": "强度",
    "stress": "应力", "stretcher": "拉伸机", "stripper": "脱模器",
    "stroke": "行程", "structural": "结构的", "strut": "支柱",
    "stud": "螺柱", "substrate": "基底", "suction": "吸入",
    "sump": "油底壳", "support": "支撑", "surface": "表面",
    "suspension": "悬挂", "switch": "开关", "synchronizer": "同步器",
    "synthesis": "综合",
    # T
    "table": "工作台", "tachometer": "转速表", "tank": "罐",
    "tap": "丝锥", "tape": "带", "taper": "锥度",
    "tapping": "攻丝", "target": "目标", "temperature": "温度",
    "tempering": "回火", "tensile": "拉伸的", "tension": "张力",
    "terminal": "端子", "test": "测试", "thermocouple": "热电偶",
    "thermodynamics": "热力学", "thermometer": "温度计", "thickness": "厚度",
    "thread": "螺纹", "throttle": "节流阀", "thrust": "推力",
    "tie": "系杆", "tilt": "倾斜", "timer": "定时器",
    "tip": "尖端", "titanium": "钛", "tolerance": "公差",
    "tool": "刀具", "tooling": "工装", "tooth": "齿",
    "torch": "焊炬", "torque": "扭矩", "torsion": "扭转",
    "tower": "塔", "track": "轨道", "tractor": "拖拉机",
    "trailer": "拖车", "transducer": "传感器", "transformer": "变压器",
    "transmission": "传动", "transport": "运输", "tray": "托盘",
    "tread": "胎面", "treatment": "处理", "tribology": "摩擦学",
    "trunnion": "耳轴", "tube": "管", "turbine": "涡轮机",
    "turbulence": "湍流", "turning": "车削",
    # U
    "ultrasonic": "超声波", "unbalance": "不平衡", "unit": "单元",
    "unloading": "卸载", "upright": "立柱", "valve": "阀门",
    "vane": "叶片", "vapor": "蒸汽", "velocity": "速度",
    "vent": "排气口", "ventilator": "通风机", "vessel": "容器",
    "vibration": "振动", "vise": "虎钳", "viscosity": "粘度",
    "voltage": "电压", "volume": "体积",
    # W
    "washer": "垫圈", "waste": "废物", "water": "水",
    "watt": "瓦特", "wear": "磨损", "web": "腹板",
    "wedge": "楔", "weight": "重量", "weld": "焊接",
    "welding": "焊接", "wheel": "车轮", "width": "宽度",
    "winch": "绞车", "wind": "风", "wire": "线材",
    "withdrawal": "抽出", "workpiece": "工件", "worm": "蜗杆",
    "wrench": "扳手",
    # X Y Z
    "yield": "屈服", "yoke": "轭架", "zinc": "锌", "zone": "区",
}

# ---- 复合词翻译规则 ----
PREFIX_TRANS = {
    "auto": "自动", "pre": "预", "post": "后", "re": "再",
    "micro": "微", "macro": "宏观", "multi": "多", "mono": "单",
    "semi": "半", "sub": "亚", "super": "超", "ultra": "超",
    "inter": "间", "intra": "内", "counter": "对", "over": "过",
    "under": "欠", "hydro": "水", "thermo": "热", "electro": "电",
    "mecha": "机械", "pneumato": "气动", "isothermal": "等温",
    "adiabatic": "绝热", "iso": "等", "poly": "多",
}

SUFFIX_TRANS = {
    "meter": "计", "scope": "镜", "graph": "图仪",
    "metry": "测量", "logy": "学", "ics": "学",
    "tion": "", "sion": "", "ment": "", "ance": "", "ence": "",
    "ing": "", "er": "器", "or": "器", "ive": "性的",
    "al": "的", "ity": "性", "ness": "性", "able": "可的",
    "less": "无的", "ful": "的",
}

def smart_translate(term):
    """Generate Chinese translation for an English term"""
    tl = term.lower().strip()
    # Direct lookup
    if tl in TRANSLATION_DICT:
        return TRANSLATION_DICT[tl]

    # Try removing trailing punctuation
    clean = re.sub(r'[\.\(\)\[\],;:!?]$', '', tl)
    if clean in TRANSLATION_DICT:
        return TRANSLATION_DICT[clean]

    # Multi-word: translate word by word
    words = re.findall(r'[a-z]+', tl)
    if len(words) >= 2:
        translations = []
        for w in words:
            if w in TRANSLATION_DICT:
                translations.append(TRANSLATION_DICT[w])
            elif len(w) > 3:
                # Try prefix analysis
                for pfx, pfx_zh in sorted(PREFIX_TRANS.items(), key=lambda x:-len(x[0])):
                    if w.startswith(pfx):
                        rest = w[len(pfx):]
                        if rest in TRANSLATION_DICT:
                            translations.append(pfx_zh + TRANSLATION_DICT[rest])
                            break
                else:
                    # Check suffix
                    for sfx, sfx_zh in sorted(SUFFIX_TRANS.items(), key=lambda x:-len(x[0])):
                        if w.endswith(sfx) and len(w) > len(sfx) + 2:
                            root = w[:-len(sfx)]
                            if root in TRANSLATION_DICT:
                                zh = TRANSLATION_DICT[root] + sfx_zh
                                translations.append(zh)
                                break
                    else:
                        translations.append(w)  # keep English
            else:
                translations.append(w)

        if any(t != w for t, w in zip(translations, words)):
            return ''.join(translations)

    return ""  # no translation found

# ---- 分类判断 ----
DOMAIN_KEYWORDS = [
    ("机械设计", ["gear", "bearing", "shaft", "spring", "bolt", "screw", "fastener",
                  "clutch", "brake", "coupling", "seal", "belt", "chain", "key", "pin",
                  "cam", "rivet", "washer", "nut", "spline", "linkage", "ratchet",
                  "tolerance", "fit", "clearance", "joint", "thread", "washer",
                  "fasten", "fixture", "jig", "clamp", "valve", "pump", "turbine"]),
    ("制造工艺", ["cast", "forge", "weld", "machin", "mill", "turn", "drill", "grind",
                 "CNC", "stamp", "extrusion", "additive", "mold", "surface", "coat",
                 "plating", "polish", "hone", "broach", "cut", "saw", "form",
                 "injection", "laser", "edm", "water jet", "blank", "die", "tool",
                 "forming", "rolling", "drawing", "anneal", "quench", "temper",
                 "carburize", "nitride", "heat treat"]),
    ("工程材料", ["steel", "alloy", "metal", "polymer", "ceramic", "composite",
                 "corrosion", "hardness", "toughness", "fatigue", "fracture",
                 "aluminum", "copper", "titanium", "nickel", "zinc", "magnesium",
                 "tungsten", "chromium", "elastic", "plasticity", "ductility",
                 "strength", "modulus", "wear", "oxidation", "aging",
                 "austenite", "ferrite", "martensite", "grain", "crystal"]),
    ("力学与强度分析", ["stress", "strain", "vibration", "finite element", "modal",
                    "tribology", "lubrication", "dynamics", "fracture", "fatigue",
                    "kinematic", "statics", "mechanics", "resonance", "frequency",
                    "friction", "deflection", "torque", "moment", "load",
                    "beam", "column", "buckling", "fatigue life"]),
    ("热工与流体", ["thermo", "fluid", "hydraulic", "pneumatic", "heat transfer",
                  "pump", "compressor", "turbine", "boiler", "condenser",
                  "evaporator", "heat exchanger", "nozzle", "diffuser",
                  "enthalpy", "entropy", "viscosity", "reynolds", "cavitation",
                  "laminar", "turbulent", "bernoulli", "engine", "combustion"]),
    ("机电自动化", ["sensor", "actuator", "servo", "robot", "automation", "control",
                 "motor", "PLC", "SCADA", "encoder", "conveyor", "AGV",
                 "mechatronics", "reducer", "gripper", "solenoid", "relay",
                 "transducer", "controller", "feedback"]),
    ("机械制图与CAD", ["CAD", "drafting", "dimension", "tolerance", "GD&T", "drawing",
                    "model", "projection", "datum", "section", "view",
                    "solid model", "parametric", "feature", "isometric",
                    "orthographic"]),
    ("标准与规范", ["ISO", "standard", "quality", "inspection", "calibration",
                  "ASTM", "DIN", "ANSI", "ASME", "SAE", "AWS", "JIS",
                  "certification", "six sigma", "lean", "gage", "gage"]),
]

def determine_category(term_en):
    tl = term_en.lower()
    for cat, keywords in DOMAIN_KEYWORDS:
        if any(kw in tl for kw in keywords):
            return cat
    return "未分类"


# ---- 定义生成 ----
DEF_TEMPLATES = {
    "机械设计": "{term}是机械设计领域的关键{kind}，广泛用于各种机械设备中",
    "制造工艺": "{term}是一种重要的制造工艺方法，用于金属或非金属材料的加工成型",
    "工程材料": "{term}是工程领域常用的材料类型，具有特定的力学性能和物理特性",
    "力学与强度分析": "{term}是固体力学中的重要概念，用于分析和描述机械结构的力学行为",
    "热工与流体": "{term}是热工流体领域的基本概念，涉及能量转换和流体运动",
    "机电自动化": "{term}是机电一体化系统中的{kind}，实现自动化控制和运动",
    "机械制图与CAD": "{term}是工程制图和计算机辅助设计中的重要概念",
    "标准与规范": "{term}是机械工程领域的标准和规范，确保产品和工艺的一致性",
    "未分类": "{term}是机械工程领域的重要概念",
}

def kind_of(cat, term_en):
    tl = term_en.lower()
    if any(w in tl for w in ["meter", "gage", "sensor", "scope", "detector", "tester"]):
        return "检测仪器"
    if any(w in tl for w in ["motor", "actuator", "driver", "pump", "compressor", "fan", "blower"]):
        return "驱动装置"
    if any(w in tl for w in ["valve", "regulator", "controller", "governor"]):
        return "控制元件"
    if any(w in tl for w in ["bearing", "gear", "shaft", "spring", "fastener", "bolt", "screw", "nut"]):
        return "机械元件"
    if any(w in tl for w in ["process", "method", "technique", "machining", "forming", "welding"]):
        return "工艺方法"
    if any(w in tl for w in ["theory", "law", "principle", "equation", "formula", "theorem"]):
        return "理论原理"
    return "概念"


def generate_definition(term_en, category, source_text=""):
    """Generate a Chinese definition for a term"""
    # Prefer source text if available and relevant
    if source_text and len(source_text) > 20:
        # Truncate to first sentence
        first_sent = re.split(r'[\.!\n]', source_text)[0][:150]
        if first_sent and len(first_sent) > 15:
            return first_sent.strip()

    template = DEF_TEMPLATES.get(category, DEF_TEMPLATES["未分类"])
    kind = kind_of(category, term_en)
    zh = smart_translate(term_en) or ""
    return template.format(term=zh or term_en, kind=kind)


# ---- 主函数 ----
def extract_terms_from_engineers_edge():
    """Extract candidate terms from Engineers-Edge titles"""
    terms = {}
    for fname in ['20260517_094615.json', '20260517_095601.json']:
        path = RAW / "engineers-edge" / fname
        data = load_json(path)
        for item in data:
            title = item.get('title', '').strip()
            text = item.get('text', '')
            if not title or len(title) < 6:
                continue

            key = title.lower()
            if key in terms:
                continue

            # Skip generic titles
            skip_words = ['calculator', 'search', 'login', 'privacy', 'disclaimer',
                         'membership', 'discussion', 'forum']
            if any(w in key for w in skip_words) and len(title) < 15:
                continue

            category = determine_category(title)
            zh = smart_translate(title)
            # Generate a brief description from the text if available
            if text:
                text_desc = text[:200].replace('\n', ' ').strip()
            else:
                text_desc = ""

            terms[key] = {
                "en": title[:80],
                "zh": zh or "",
                "source": "engineers_edge",
                "category": category,
                "description": generate_definition(title, category, text_desc)[:200]
            }
    return terms


def extract_terms_from_efunda():
    terms = {}
    for fname in ['20260517_094451.json']:
        path = RAW / "efunda" / fname
        data = load_json(path)
        for item in data:
            title = item.get('title', '').strip()
            text = item.get('content', '')
            if not title or len(title) < 6:
                continue
            key = title.lower()
            if key in terms:
                continue
            skip_words = ['search', 'login', 'privacy', 'disclaimer', 'membership']
            if any(w in key for w in skip_words):
                continue

            category = determine_category(title)
            zh = smart_translate(title)
            if text:
                text_desc = text[:200].replace('\n', ' ').strip()
            else:
                text_desc = ""

            terms[key] = {
                "en": title[:80],
                "zh": zh,
                "source": "efunda",
                "category": category,
                "description": generate_definition(title, category, text_desc)[:200]
            }
    return terms


def extract_terms_from_eng_toolbox():
    terms = {}
    for fname in ['20260517_092143.json']:
        path = RAW / "engineering-toolbox" / fname
        data = load_json(path)
        for item in data:
            title = item.get('title', '').strip()
            text = item.get('content', item.get('text', ''))
            if not title or len(title) < 6:
                continue
            key = title.lower()
            if key in terms:
                continue
            category = determine_category(title)
            zh = smart_translate(title)
            if text:
                text_desc = text[:200].replace('\n', ' ').strip()
            else:
                text_desc = ""
            terms[key] = {
                "en": title[:80],
                "zh": zh,
                "source": "engineering_toolbox",
                "category": category,
                "description": generate_definition(title, category, text_desc)[:200]
            }
    return terms


def extract_terms_from_wikipedia(wp_data):
    """Extract terms from Wikipedia page data"""
    terms = {}
    pages = wp_data.get("all_pages", [])
    for page in pages:
        title = page.get('title', '').strip()
        extract = page.get('extract', '')
        if not title:
            continue
        key = title.lower()
        if key in terms:
            continue
        category = determine_category(title)
        zh = smart_translate(title)
        terms[key] = {
            "en": title[:80],
            "zh": zh,
            "source": "wikipedia",
            "category": category,
            "description": generate_definition(title, category, extract)[:200]
        }
    return terms


def extract_subterms(text, existing_terms):
    """Extract additional sub-terms from text content (bigrams, trigrams)"""
    new_terms = {}
    if not text:
        return new_terms
    # Find capitalized technical phrases
    phrases = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b', text)
    for phrase in phrases:
        key = phrase.lower()
        if key in existing_terms or len(key) < 5:
            continue
        # Avoid picking up common English phrases
        if any(w in key for w in ['this', 'that', 'with', 'from', 'the', 'and', 'for']):
            continue
        category = determine_category(key)
        zh = smart_translate(phrase)
        new_terms[key] = {
            "en": phrase[:80],
            "zh": zh,
            "source": "subterm_extraction",
            "category": category,
            "description": generate_definition(phrase, category)[:200]
        }
    return new_terms


def main():
    print("B11: 机械工程术语表扩展至5000+条", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    # Step 1: Load existing terminology
    existing_terms, existing_extras = load_existing_terms()
    print(f"现有术语: {len(existing_terms)} 核心 + {len(existing_extracts)} 自动提取",
          file=sys.stderr)

    # Step 2: Extract from ALL raw data sources
    print("\n从原始数据源提取...", file=sys.stderr)

    ee_terms = extract_terms_from_engineers_edge()
    print(f"  Engineers-Edge: {len(ee_terms)} 候选术语", file=sys.stderr)

    efunda_terms = extract_terms_from_efunda()
    print(f"  eFunda: {len(efunda_terms)} 候选术语", file=sys.stderr)

    et_terms = extract_terms_from_eng_toolbox()
    print(f"  Engineering-Toolbox: {len(et_terms)} 候选术语", file=sys.stderr)

    # Wikipedia (if not already fully processed)
    wp_data = json.loads((KB / "wikipedia-pages.json").read_text()) if (KB / "wikipedia-pages.json").exists() else {}
    wp_terms = extract_terms_from_wikipedia(wp_data)
    print(f"  Wikipedia: {len(wp_terms)} 候选术语", file=sys.stderr)

    # Step 3: Merge all terms into unified dictionary
    all_terms = {}

    # Add existing seed terms first
    for key, t in existing_terms.items():
        all_terms[key] = dict(t)
        all_terms[key]["source"] = "seed_dictionary"
        # Add definition if not present
        if "description" not in all_terms[key]:
            all_terms[key]["description"] = generate_definition(t["en"], t.get("category","未分类"))

    # Add existing extracted terms
    for key, t in existing_extras.items():
        if key not in all_terms:
            all_terms[key] = dict(t)
            if "description" not in all_terms[key]:
                all_terms[key]["description"] = generate_definition(t["en"], t.get("category","未分类"))

    # Merge new raw source terms (only if not already present)
    for src_dict, src_name in [
        (wp_terms, "wikipedia"), (ee_terms, "engineers_edge"),
        (efunda_terms, "efunda"), (et_terms, "engineering_toolbox")
    ]:
        for key, t in src_dict.items():
            if key not in all_terms:
                all_terms[key] = t

    # Step 4: Extract sub-terms from source texts (for additional coverage)
    sub_terms = {}
    for src_dict in [ee_terms, efunda_terms, et_terms]:
        for key, t in src_dict.items():
            text = t.get('description', '')
            sub = extract_subterms(text, all_terms)
            sub_terms.update(sub)
    print(f"  子词提取: {len(sub_terms)} 候选术语", file=sys.stderr)

    for key, t in sub_terms.items():
        if key not in all_terms:
            all_terms[key] = t

    # Step 5: Generate remaining Chinese translations for all terms without zh
    untranslated = 0
    for key, t in all_terms.items():
        if not t.get("zh"):
            zh = smart_translate(t["en"])
            if zh:
                t["zh"] = zh
            else:
                untranslated += 1

    print(f"\n未翻译术语: {untranslated}", file=sys.stderr)

    # Step 6: Categorize uncategorized
    uncategorized = 0
    for key, t in all_terms.items():
        if t.get("category") in ("未分类", "core", None, ""):
            cat = determine_category(t["en"])
            if cat != "未分类":
                t["category"] = cat
            else:
                uncategorized += 1

    print(f"未分类术语: {uncategorized}", file=sys.stderr)

    # Step 7: Output structured JSON
    seed_list = [v for v in all_terms.values() if v.get("source") == "seed_dictionary"]
    extracted_list = [v for v in all_terms.values() if v.get("source") != "seed_dictionary"]

    # Sort by category then English
    seed_list.sort(key=lambda t: (t.get("category","未分类"), t["en"]))
    extracted_list.sort(key=lambda t: (t.get("category","未分类"), t["en"]))

    # Categorize
    cat_counts = Counter(t.get("category","未分类") for t in all_terms.values())

    output = {
        "meta": {
            "title": "机械工程中英术语对照表V3",
            "version": "3.0",
            "created": "2026-05-18",
            "total_terms": len(all_terms),
            "seed_terms": len(seed_list),
            "extracted_terms": len(extracted_list),
            "data_sources": [
                "seed_dictionary", "wikipedia", "mit_ocw",
                "engineering_portals", "engineers_edge", "efunda",
                "engineering_toolbox", "subterm_extraction"
            ],
            "category_distribution": dict(cat_counts.most_common())
        },
        "terms": seed_list,
        "extracted_extras": extracted_list
    }

    # Write JSON
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\nJSON: {OUTPUT_JSON}", file=sys.stderr)

    # Step 8: Generate Markdown
    cat_order = ["工程材料", "力学与强度分析", "机械设计", "制造工艺",
                 "热工与流体", "机电自动化", "机械制图与CAD", "标准与规范", "未分类"]

    md_lines = [
        "# 机械工程中英术语对照表 V3\n",
        f"> 版本 3.0 | 2026-05-18 | 总计 {len(all_terms)} 条术语\n",
        f"> 核心词典 {len(seed_list)} 条 + 自动提取 {len(extracted_list)} 条\n",
        f"> 数据来源: {', '.join(output['meta']['data_sources'])}\n",
        "---\n",
    ]

    # Category distribution
    md_lines.append("\n## 分类分布\n")
    md_lines.append("| 分类 | 术语数量 |\n|------|---------|\n")
    for cat in cat_order:
        cnt = cat_counts.get(cat, 0)
        if cnt > 0:
            md_lines.append(f"| {cat} | {cnt} |\n")

    # Main term table (with Chinese translations)
    md_lines.append("\n## 核心术语（含中英文翻译）\n")
    md_lines.append("| 英文 | 中文 | 分类 |\n|------|------|------|\n")
    for t in seed_list:
        md_lines.append(f"| {t['en']} | {t.get('zh','')} | {t.get('category','未分类')} |\n")

    md_lines.append(f"\n## 自动提取词条（{len(extracted_list)} 条）\n")
    md_lines.append("| 英文 | 中文 | 分类 | 来源 |\n|------|------|------|------|\n")
    for t in extracted_list[:500]:  # top 500 in MD
        md_lines.append(f"| {t['en'][:60]} | {t.get('zh','')[:30]} | {t.get('category','未分类')} | {t.get('source','')} |\n")

    if len(extracted_list) > 500:
        md_lines.append(f"\n> 注: Markdown仅显示前500条自动提取，完整{len(extracted_list)}条见JSON文件\n")

    OUTPUT_MD.write_text("".join(md_lines))
    print(f"MD:   {OUTPUT_MD}", file=sys.stderr)

    # Summary
    print("\n" + "=" * 50, file=sys.stderr)
    print(f"总计: {len(all_terms)} 条术语", file=sys.stderr)
    print(f"  核心(含中文): {len(seed_list)}", file=sys.stderr)
    print(f"  自动提取: {len(extracted_list)}", file=sys.stderr)
    for cat, cnt in cat_counts.most_common():
        print(f"  {cat}: {cnt}", file=sys.stderr)

if __name__ == "__main__":
    # Need to define existing_extracts before calling main
    existing_terms, existing_extracts = load_existing_terms()
    main()
