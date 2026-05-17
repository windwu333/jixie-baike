#!/usr/bin/env python3
"""扩展机械工程术语表至5000+条，合并所有数据源"""
import json, re, sys
from pathlib import Path

BASE = Path(__file__).parent.parent
KB = BASE / "knowledge-base"
OUTPUT_JSON = KB / "mech-terminology-v2.json"
OUTPUT_MD = KB / "mech-terminology-v2.md"

# Load existing terminology
existing = json.loads((KB / "mech-terminology.json").read_text()) if (KB / "mech-terminology.json").exists() else {"terms":[], "extracted_extras":[]}
wikipages = json.loads((KB / "wikipedia-pages.json").read_text()) if (KB / "wikipedia-pages.json").exists() else {"all_pages":[]}
mitocw = json.loads((KB / "mit-ocw-courses.json").read_text()) if (KB / "mit-ocw-courses.json").exists() else {"courses":[]}
engdata = json.loads((KB / "engineering-portals-data.json").read_text()) if (KB / "engineering-portals-data.json").exists() else {"sites":[]}
standards = json.loads((KB / "gb-iso-standards.json").read_text()) if (KB / "gb-iso-standards.json").exists() else {"standards":[]}

# Large seed dictionary (~800 core terms across all categories)
SEED_TERMS = {
    # === 材料 (Materials) — 80+ ===
    "steel": "钢", "alloy steel": "合金钢", "carbon steel": "碳钢", "tool steel": "工具钢",
    "stainless steel": "不锈钢", "spring steel": "弹簧钢", "bearing steel": "轴承钢",
    "cast iron": "铸铁", "ductile iron": "球墨铸铁", "gray iron": "灰铸铁",
    "white iron": "白口铸铁", "malleable iron": "可锻铸铁",
    "aluminum": "铝", "aluminum alloy": "铝合金", "copper": "铜", "copper alloy": "铜合金",
    "brass": "黄铜", "bronze": "青铜", "phosphor bronze": "磷青铜",
    "titanium": "钛", "titanium alloy": "钛合金", "nickel": "镍",
    "nickel alloy": "镍合金", "inconel": "因科镍合金",
    "zinc": "锌", "zinc alloy": "锌合金", "magnesium": "镁", "magnesium alloy": "镁合金",
    "tin": "锡", "lead": "铅", "tungsten": "钨", "cobalt": "钴",
    "chromium": "铬", "molybdenum": "钼", "vanadium": "钒", "manganese": "锰",
    "silicon": "硅", "niobium": "铌",
    "polymer": "聚合物", "polyethylene": "聚乙烯", "polypropylene": "聚丙烯",
    "nylon": "尼龙", "polycarbonate": "聚碳酸酯", "acetal": "聚甲醛",
    "PTFE": "聚四氟乙烯", "ABS": "ABS塑料", "PVC": "聚氯乙烯",
    "acrylic": "亚克力", "polyurethane": "聚氨酯",
    "composite": "复合材料", "carbon fiber": "碳纤维", "fiberglass": "玻璃纤维",
    "ceramic": "陶瓷", "alumina": "氧化铝陶瓷", "zirconia": "氧化锆陶瓷",
    "silicon carbide": "碳化硅", "tungsten carbide": "碳化钨",
    "metal matrix composite": "金属基复合材料",
    "heat treatment": "热处理", "annealing": "退火", "normalizing": "正火",
    "quenching": "淬火", "tempering": "回火", "carburizing": "渗碳",
    "nitriding": "渗氮", "carbonitriding": "碳氮共渗",
    "induction hardening": "感应淬火", "flame hardening": "火焰淬火",
    "solution treatment": "固溶处理", "aging treatment": "时效处理",
    "cryogenic treatment": "深冷处理",
    "hardness": "硬度", "hardness test": "硬度测试", "rockwell hardness": "洛氏硬度",
    "brinell hardness": "布氏硬度", "vickers hardness": "维氏硬度",
    "toughness": "韧性", "ductility": "延展性", "malleability": "可锻性",
    "brittleness": "脆性", "elasticity": "弹性", "plasticity": "塑性",
    "fatigue": "疲劳", "creep": "蠕变", "wear resistance": "耐磨性",
    "corrosion resistance": "耐腐蚀性",
    "yield strength": "屈服强度", "tensile strength": "抗拉强度",
    "compressive strength": "抗压强度", "shear strength": "抗剪强度",
    "fatigue strength": "疲劳强度", "impact strength": "冲击强度",
    "elastic modulus": "弹性模量", "young's modulus": "杨氏模量",
    "shear modulus": "剪切模量", "bulk modulus": "体积模量",
    "poisson's ratio": "泊松比", "density": "密度",
    "corrosion": "腐蚀", "wear": "磨损", "oxidation": "氧化",

    # === 力学 (Mechanics) — 70+ ===
    "stress": "应力", "normal stress": "正应力", "shear stress": "剪应力",
    "principal stress": "主应力", "von mises stress": "冯·米塞斯应力",
    "thermal stress": "热应力", "residual stress": "残余应力",
    "bending stress": "弯曲应力", "contact stress": "接触应力",
    "stress concentration": "应力集中", "stress intensity factor": "应力强度因子",
    "strain": "应变", "normal strain": "正应变", "shear strain": "剪应变",
    "strain energy": "应变能", "plane stress": "平面应力", "plane strain": "平面应变",
    "bending": "弯曲", "pure bending": "纯弯曲", "torsion": "扭转",
    "axial loading": "轴向载荷", "eccentric loading": "偏载",
    "static loading": "静载荷", "dynamic loading": "动载荷",
    "cyclic loading": "循环载荷", "impact loading": "冲击载荷",
    "fatigue loading": "疲劳载荷",
    "vibration": "振动", "free vibration": "自由振动",
    "forced vibration": "受迫振动", "damped vibration": "阻尼振动",
    "natural frequency": "固有频率", "resonance": "共振",
    "mode shape": "振型", "modal analysis": "模态分析",
    "harmonic analysis": "谐响应分析",
    "finite element": "有限元", "finite element analysis": "有限元分析",
    "FEA": "有限元分析", "finite element method": "有限元法",
    "mesh": "网格", "element": "单元", "node": "节点",
    "fatigue life": "疲劳寿命", "fracture": "断裂",
    "fracture mechanics": "断裂力学", "crack propagation": "裂纹扩展",
    "crack initiation": "裂纹萌生", "fracture toughness": "断裂韧性",
    "tribology": "摩擦学", "friction": "摩擦", "lubrication": "润滑",
    "hydrodynamic lubrication": "流体动压润滑", "elastohydrodynamic lubrication": "弹流润滑",
    "boundary lubrication": "边界润滑", "wear mechanism": "磨损机理",
    "abrasive wear": "磨粒磨损", "adhesive wear": "粘着磨损",
    "fatigue wear": "疲劳磨损", "corrosive wear": "腐蚀磨损",
    "erosion": "冲蚀", "cavitation": "空蚀",
    "dynamics": "动力学", "kinematics": "运动学", "kinetics": "动力学",
    "statics": "静力学", "strength of materials": "材料力学",
    "theoretical mechanics": "理论力学", "mechanics of materials": "材料力学",
    "solid mechanics": "固体力学", "rigid body": "刚体",
    "degree of freedom": "自由度", "moment of inertia": "惯性矩",
    "section modulus": "截面模量", "radius of gyration": "回转半径",

    # === 机械设计 (Machine Design) — 140+ ===
    "gear": "齿轮", "spur gear": "直齿轮", "helical gear": "斜齿轮",
    "bevel gear": "锥齿轮", "worm gear": "蜗杆蜗轮", "worm": "蜗杆",
    "gear rack": "齿条", "ring gear": "齿圈", "planetary gear": "行星齿轮",
    "sun gear": "太阳轮", "pinion": "小齿轮", "gear train": "轮系",
    "gear ratio": "传动比", "module": "模数", "pressure angle": "压力角",
    "involute": "渐开线", "addendum": "齿顶高", "dedendum": "齿根高",
    "clearance": "顶隙",
    "bearing": "轴承", "ball bearing": "球轴承",
    "roller bearing": "滚子轴承", "tapered roller bearing": "圆锥滚子轴承",
    "needle bearing": "滚针轴承", "thrust bearing": "推力轴承",
    "angular contact bearing": "角接触球轴承", "self-aligning bearing": "调心轴承",
    "plain bearing": "滑动轴承", "journal bearing": "径向滑动轴承",
    "hydrostatic bearing": "静压轴承", "magnetic bearing": "磁悬浮轴承",
    "bearing clearance": "轴承间隙", "bearing preload": "轴承预紧",
    "shaft": "轴", "transmission shaft": "传动轴", "spindle": "主轴",
    "crankshaft": "曲轴", "camshaft": "凸轮轴", "axle": "车轴",
    "shaft shoulder": "轴肩", "keyway": "键槽",
    "coupling": "联轴器", "rigid coupling": "刚性联轴器",
    "flexible coupling": "弹性联轴器", "fluid coupling": "液力偶合器",
    "clutch": "离合器", "friction clutch": "摩擦离合器",
    "centrifugal clutch": "离心离合器", "overrunning clutch": "超越离合器",
    "brake": "制动器", "disc brake": "盘式制动器", "drum brake": "鼓式制动器",
    "band brake": "带式制动器", "spring brake": "弹簧制动器",
    "belt drive": "带传动", "flat belt": "平带", "v-belt": "V带",
    "timing belt": "同步带", "ribbed belt": "多楔带",
    "chain drive": "链传动", "roller chain": "滚子链", "silent chain": "无声链",
    "sprocket": "链轮",
    "spring": "弹簧", "compression spring": "压缩弹簧",
    "extension spring": "拉伸弹簧", "torsion spring": "扭转弹簧",
    "coil spring": "螺旋弹簧", "leaf spring": "板弹簧", "belleville spring": "碟形弹簧",
    "wave spring": "波形弹簧", "constant force spring": "恒力弹簧",
    "seal": "密封", "mechanical seal": "机械密封", "oil seal": "油封",
    "oring": "O形密封圈", "gasket": "垫片", "packing": "填料密封",
    "labyrinth seal": "迷宫密封",
    "fastener": "紧固件", "bolt": "螺栓", "stud bolt": "双头螺柱",
    "nut": "螺母", "lock nut": "防松螺母", "wing nut": "蝶形螺母",
    "screw": "螺钉", "set screw": "紧定螺钉", "machine screw": "机用螺钉",
    "self-tapping screw": "自攻螺钉",
    "washer": "垫圈", "spring washer": "弹簧垫圈", "lock washer": "止动垫圈",
    "key": "键", "flat key": "平键", "woodruff key": "半圆键",
    "spline": "花键", "pin": "销", "dowel pin": "定位销", "cotter pin": "开口销",
    "rivet": "铆钉", "weld": "焊接", "solder": "钎焊",
    "adhesive bonding": "粘接",
    "cam": "凸轮", "cam follower": "凸轮从动件", "eccentric": "偏心轮",
    "linkage": "连杆机构", "four-bar linkage": "四杆机构",
    "slider-crank": "曲柄滑块机构", "geneva mechanism": "槽轮机构",
    "ratchet": "棘轮机构",
    "tolerance": "公差", "dimensional tolerance": "尺寸公差",
    "geometric tolerance": "几何公差", "fit": "配合",
    "clearance fit": "间隙配合", "interference fit": "过盈配合",
    "transition fit": "过渡配合", "limit": "极限尺寸",
    "surface roughness": "表面粗糙度", "Ra": "轮廓算术平均偏差",
    "Rz": "微观不平度十点高度",
    "assembly": "装配", "exploded view": "爆炸图",
    "section view": "剖视图", "detail drawing": "零件图",
    "general assembly drawing": "总装图",

    # === 制造工艺 (Manufacturing) — 100+ ===
    "casting": "铸造", "sand casting": "砂型铸造", "investment casting": "熔模铸造",
    "die casting": "压铸", "centrifugal casting": "离心铸造",
    "continuous casting": "连续铸造", "lost foam casting": "消失模铸造",
    "gravity casting": "重力铸造", "shell molding": "壳型铸造",
    "pattern": "模样", "core": "型芯", "mold": "铸型", "riser": "冒口",
    "gating system": "浇注系统", "runner": "横浇道", "gate": "内浇道",
    "forging": "锻造", "open die forging": "自由锻",
    "closed die forging": "模锻", "drop forging": "落锤锻造",
    "upset forging": "镦粗", "hot forging": "热锻", "cold forging": "冷锻",
    "warm forging": "温锻", "coining": "精压",
    "press forging": "压力机锻造", "roll forging": "辊锻",
    "machining": "机械加工", "turning": "车削", "milling": "铣削",
    "drilling": "钻孔", "boring": "镗削", "reaming": "铰孔",
    "tapping": "攻丝", "threading": "车螺纹",
    "grinding": "磨削", "surface grinding": "平面磨削",
    "cylindrical grinding": "外圆磨削", "centerless grinding": "无心磨削",
    "honing": "珩磨", "lapping": "研磨", "polishing": "抛光",
    "broaching": "拉削", "planing": "刨削", "shaping": "插削",
    "sawing": "锯削", "slotting": "开槽",
    "CNC": "数控", "CNC milling": "数控铣", "CNC turning": "数控车",
    "machining center": "加工中心", "flexible manufacturing": "柔性制造",
    "cutting speed": "切削速度", "feed rate": "进给速度", "depth of cut": "切削深度",
    "cutting tool": "切削刀具", "cutting fluid": "切削液",
    "carbide tool": "硬质合金刀具", "high speed steel": "高速钢",
    "coated tool": "涂层刀具",
    "additive manufacturing": "增材制造", "3D printing": "3D打印",
    "FDM": "熔融沉积成型", "SLA": "光固化成型", "SLS": "选择性激光烧结",
    "SLM": "选择性激光熔化", "EBM": "电子束熔化",
    "stamping": "冲压", "blanking": "落料", "piercing": "冲孔",
    "bending": "折弯", "deep drawing": "深拉深", "forming": "成型",
    "extrusion": "挤压", "direct extrusion": "正挤压", "indirect extrusion": "反挤压",
    "hydroforming": "液压成型", "spinning": "旋压",
    "rolling": "轧制", "hot rolling": "热轧", "cold rolling": "冷轧",
    "wire drawing": "拉丝", "tube drawing": "拉管",
    "surface treatment": "表面处理", "coating": "涂层",
    "painting": "喷涂", "powder coating": "粉末喷涂",
    "electroplating": "电镀", "chrome plating": "镀铬", "zinc plating": "镀锌",
    "nickel plating": "镀镍", "anodizing": "阳极氧化",
    "phosphating": "磷化处理", "passivation": "钝化处理",
    "heat treatment coating": "热喷涂", "PVD": "物理气相沉积",
    "CVD": "化学气相沉积",
    "injection molding": "注塑成型",
    "compression molding": "模压成型", "blow molding": "吹塑成型",
    "thermoforming": "热成型",
    "water jet cutting": "水切割", "laser cutting": "激光切割",
    "plasma cutting": "等离子切割", "EDM": "电火花加工",
    "wire EDM": "线切割", "ultrasonic machining": "超声波加工",
    "chemical machining": "化学加工",

    # === 热工流体 (Thermal & Fluids) — 80+ ===
    "thermodynamics": "热力学", "thermodynamic cycle": "热力循环",
    "carnot cycle": "卡诺循环", "rankine cycle": "朗肯循环",
    "otto cycle": "奥托循环", "diesel cycle": "狄塞尔循环",
    "brayton cycle": "布雷顿循环", "stirling cycle": "斯特林循环",
    "enthalpy": "焓", "entropy": "熵", "internal energy": "内能",
    "specific heat capacity": "比热容",
    "heat transfer": "传热", "conduction": "热传导", "convection": "热对流",
    "radiation": "热辐射", "heat flux": "热流密度",
    "thermal conductivity": "热导率", "thermal resistance": "热阻",
    "heat exchanger": "换热器", "shell and tube": "管壳式换热器",
    "plate heat exchanger": "板式换热器", "fin": "翅片",
    "boiler": "锅炉", "steam generator": "蒸汽发生器",
    "condenser": "冷凝器", "evaporator": "蒸发器",
    "cooling tower": "冷却塔", "radiator": "散热器",
    "fluid mechanics": "流体力学",
    "fluid statics": "流体静力学", "fluid dynamics": "流体动力学",
    "laminar flow": "层流", "turbulent flow": "湍流",
    "reynolds number": "雷诺数", "bernoulli equation": "伯努利方程",
    "continuity equation": "连续性方程", "navier-stokes equations": "纳维-斯托克斯方程",
    "boundary layer": "边界层", "viscosity": "粘度",
    "dynamic viscosity": "动力粘度", "kinematic viscosity": "运动粘度",
    "cavitation": "空化", "compressible flow": "可压缩流",
    "hydraulics": "液压", "hydraulic system": "液压系统",
    "hydraulic pump": "液压泵", "hydraulic cylinder": "液压缸",
    "hydraulic motor": "液压马达", "hydraulic valve": "液压阀",
    "directional control valve": "方向控制阀", "pressure relief valve": "溢流阀",
    "flow control valve": "流量控制阀",
    "accumulator": "蓄能器", "filter": "过滤器",
    "pneumatics": "气动", "pneumatic system": "气动系统",
    "air compressor": "空气压缩机", "pneumatic cylinder": "气缸",
    "solenoid valve": "电磁阀",
    "pump": "泵", "centrifugal pump": "离心泵",
    "gear pump": "齿轮泵", "piston pump": "柱塞泵",
    "diaphragm pump": "隔膜泵", "peristaltic pump": "蠕动泵",
    "screw pump": "螺杆泵", "vane pump": "叶片泵",
    "valve": "阀门", "gate valve": "闸阀", "globe valve": "截止阀",
    "ball valve": "球阀", "butterfly valve": "蝶阀", "check valve": "止回阀",
    "relief valve": "安全阀", "control valve": "调节阀",
    "compressor": "压缩机", "reciprocating compressor": "往复式压缩机",
    "centrifugal compressor": "离心式压缩机", "screw compressor": "螺杆压缩机",
    "turbine": "涡轮机", "steam turbine": "汽轮机", "gas turbine": "燃气轮机",
    "hydraulic turbine": "水轮机", "wind turbine": "风力发电机",
    "internal combustion engine": "内燃机",
    "spark ignition engine": "点燃式发动机", "compression ignition engine": "压燃式发动机",
    "four stroke engine": "四冲程发动机", "two stroke engine": "二冲程发动机",
    "nozzle": "喷嘴", "diffuser": "扩压器",

    # === 机电自动化 (Mechatronics) — 80+ ===
    "sensor": "传感器", "temperature sensor": "温度传感器",
    "pressure sensor": "压力传感器", "flow sensor": "流量传感器",
    "position sensor": "位置传感器", "proximity sensor": "接近开关",
    "limit switch": "限位开关", "photoelectric sensor": "光电传感器",
    "encoder": "编码器", "rotary encoder": "旋转编码器",
    "linear encoder": "光栅尺",
    "strain gauge": "应变片", "load cell": "测力传感器",
    "thermocouple": "热电偶", "RTD": "热电阻",
    "accelerometer": "加速度计", "gyroscope": "陀螺仪",
    "vision sensor": "视觉传感器", "laser sensor": "激光传感器",
    "actuator": "执行器", "electric actuator": "电动执行器",
    "hydraulic actuator": "液压执行器", "pneumatic actuator": "气动执行器",
    "linear actuator": "直线执行器",
    "motor": "电机", "DC motor": "直流电机", "AC motor": "交流电机",
    "induction motor": "感应电机", "synchronous motor": "同步电机",
    "brushless DC motor": "无刷直流电机",
    "servo motor": "伺服电机", "stepper motor": "步进电机",
    "linear motor": "直线电机", "torque motor": "力矩电机",
    "reducer": "减速器", "gear reducer": "齿轮减速器",
    "planetary reducer": "行星减速器", "harmonic drive": "谐波减速器",
    "RV reducer": "RV减速器",
    "PLC": "可编程逻辑控制器",
    "DCS": "集散控制系统", "SCADA": "数据采集与监控系统",
    "robot": "机器人", "industrial robot": "工业机器人",
    "collaborative robot": "协作机器人", "robot arm": "机械臂",
    "end effector": "末端执行器", "gripper": "夹爪",
    "automation": "自动化", "mechatronics": "机电一体化",
    "control system": "控制系统", "feedback control": "反馈控制",
    "open loop": "开环", "closed loop": "闭环",
    "PID control": "PID控制", "servo control": "伺服控制",
    "motion control": "运动控制", "CNC control": "数控系统",
    "conveyor": "输送机", "conveyor belt": "传送带",
    "AGV": "自动导引车", "palletizer": "码垛机",
    "pick and place": "拾放操作",

    # === 制图CAD (Drafting & CAD) — 50+ ===
    "CAD": "计算机辅助设计", "computer-aided design": "计算机辅助设计",
    "CAD/CAM": "CAD/CAM", "CAM": "计算机辅助制造",
    "CAE": "计算机辅助工程", "CAPP": "计算机辅助工艺规划",
    "solid modeling": "实体建模", "surface modeling": "曲面建模",
    "wireframe": "线框", "parametric modeling": "参数化建模",
    "feature-based modeling": "特征建模",
    "3D model": "三维模型", "2D drawing": "二维图",
    "section": "剖面", "section line": "剖切线",
    "auxiliary view": "辅助视图", "isometric view": "轴测图",
    "detail view": "局部放大图", "orthographic projection": "正交投影",
    "first angle projection": "第一角投影", "third angle projection": "第三角投影",
    "dimension": "尺寸", "baseline dimensioning": "基准标注",
    "chain dimensioning": "链式标注", "ordinate dimensioning": "坐标标注",
    "GD&T": "几何尺寸与公差",
    "true position": "位置度", "runout": "圆跳动",
    "concentricity": "同轴度", "symmetry": "对称度",
    "parallelism": "平行度", "perpendicularity": "垂直度",
    "flatness": "平面度", "straightness": "直线度",
    "roundness": "圆度", "cylindricity": "圆柱度",
    "angularity": "倾斜度", "profile": "轮廓度",
    "datum": "基准", "datum feature": "基准特征",
    "title block": "标题栏", "bill of materials": "材料明细表",
    "part number": "零件编号",

    # === 标准规范 (Standards) — 40+ ===
    "ISO": "国际标准化组织", "ISO standard": "ISO标准",
    "ASTM": "美国材料与试验协会", "ASTM standard": "ASTM标准",
    "DIN": "德国标准", "DIN standard": "DIN标准",
    "JIS": "日本工业标准", "GB standard": "中国国家标准",
    "GB/T": "中国推荐性国家标准",
    "ANSI": "美国国家标准", "SAE": "美国汽车工程师协会",
    "ASME": "美国机械工程师协会", "ASME standard": "ASME标准",
    "AWS": "美国焊接协会",
    "quality control": "质量控制", "quality assurance": "质量保证",
    "SPC": "统计过程控制", "CPK": "过程能力指数",
    "inspection": "检验", "sampling inspection": "抽样检验",
    "non-destructive testing": "无损检测", "NDT": "无损检测",
    "ultrasonic testing": "超声波检测", "radiographic testing": "射线检测",
    "magnetic particle testing": "磁粉检测", "dye penetrant testing": "渗透检测",
    "eddy current testing": "涡流检测",
    "calibration": "校准", "traceability": "可追溯性",
    "certification": "认证", "ISO 9000": "ISO 9000质量管理体系",
    "ISO 14000": "ISO 14000环境管理体系",
    "six sigma": "六西格玛", "lean manufacturing": "精益制造",
    "total quality management": "全面质量管理",
    "five why": "5Why分析法", "fishbone diagram": "鱼骨图",
    "Pareto chart": "帕累托图", "control chart": "控制图",
}

def extract_terms_from_pages(wp_data, mit_data, eng_data):
    """Extract candidate English terms from all data sources"""
    candidates = {}

    # From Wikipedia page titles
    for page in wp_data.get("all_pages", []):
        title = page["title"]
        candidates[title.lower()] = {"en": title, "source": "wikipedia"}

    # From MIT OCW course titles
    for course in mit_data.get("courses", []):
        title = course.get("title", "")
        for word in re.findall(r'\b[A-Z][a-z]+(?:\s+[a-z]+)*\b', title):
            if len(word) > 4 and word.lower() not in candidates:
                candidates[word.lower()] = {"en": word, "source": "mit_ocw"}

    # From engineering portal page titles
    for site in eng_data.get("sites", []):
        for page in site.get("pages", []):
            title = page.get("title", "")
            candidates[title.lower()] = {"en": title, "source": "engineering_portal"}

    return candidates

def determine_category(term):
    """Determine category based on keywords"""
    tl = term.lower()
    cat_map = [
        (["gear", "bearing", "shaft", "spring", "bolt", "screw", "fastener",
          "clutch", "brake", "coupling", "valve", "pump", "seal", "belt",
          "chain", "key", "pin", "cam", "rivet", "washer", "nut", "spline",
          "linkage", "ratchet", "tolerance", "fit", "compress", "extension",
          "torsion", "bearing"], "机械设计"),
        (["steel", "alloy", "metal", "polymer", "ceramic", "composite",
          "corrosion", "heat treatment", "hardness", "fatigue", "fracture",
          "aluminum", "copper", "titanium", "nickel", "zinc", "magnesium",
          "tungsten", "chromium", "hardness", "toughness", "ductility",
          "elasticity", "plasticity", "strength", "modulus", "anneal",
          "quench", "temper", "carburize", "nitride", "wear", "oxidation",
          "aging", "solution treatment", "cryogenic"], "工程材料"),
        (["cast", "forge", "weld", "machin", "mill", "turn", "drill",
          "grind", "CNC", "stamp", "extrusion", "additive", "3d print",
          "mold", "surface", "coating", "plating", "polish", "hone",
          "broach", "cut", "saw", "form", "draw", "roll", "metalwork",
          "injection mold", "laser cut", "edm", "water jet"], "制造工艺"),
        (["thermo", "fluid", "hydraulic", "pneumatic", "heat transfer",
          "pump", "compressor", "turbine", "boiler", "condenser",
          "evaporator", "heat exchanger", "nozzle", "diffuser",
          "enthalpy", "entropy", "viscosity", "reynolds", "cavitation",
          "laminar", "turbulent", "bernoulli", "engine"], "热工流体"),
        (["sensor", "actuator", "servo", "robot", "automation", "control",
          "motor", "PLC", "SCADA", "encoder", "conveyor", "AGV",
          "mechatronics", "reducer", "gripper"], "机电自动化"),
        (["stress", "strain", "vibration", "finite element", "modal",
          "tribology", "lubrication", "dynamics", "fracture", "fatigue",
          "kinematic", "statics", "mechanics", "resonance", "natural frequency",
          "friction", "wear", "erosion"], "力学强度"),
        (["CAD", "drafting", "dimension", "tolerance", "GD&T", "drawing",
          "model","projection", "datum", "section", "view",
          "solid model", "parametric", "feature"], "制图CAD"),
        (["ISO", "standard", "quality", "inspection", "calibration",
          "ASTM", "DIN", "ANSI", "ASME", "SAE", "AWS", "JIS",
          "certification", "six sigma", "lean"], "标准规范"),
    ]

    for keywords, cat in cat_map:
        if any(kw in tl for kw in keywords):
            return cat
    return "未分类"

def main():
    # Build seed dictionary
    terminology = {}
    for eng, chn in SEED_TERMS.items():
        terminology[eng.lower()] = {
            "en": eng, "zh": chn,
            "source": "seed", "category": determine_category(eng)
        }

    # Extract candidates from data sources
    candidates = extract_terms_from_pages(wikipages, mitocw, engdata)

    # Add candidates not in seed
    for key, cand in candidates.items():
        if key not in terminology and len(key) > 3:
            cat = determine_category(cand["en"])
            terminology[key] = {
                "en": cand["en"][:80], "zh": "",
                "source": cand["source"], "category": cat
            }

    # Categorize and sort
    seed_list = [v for v in terminology.values() if v["source"] == "seed"]
    extracted_list = [v for v in terminology.values() if v["source"] != "seed"]

    output = {
        "meta": {
            "title": "机械工程中英术语对照表V2",
            "version": "2.0",
            "created": "2026-05-17",
            "total_terms": len(terminology),
            "seed_terms": len(seed_list),
            "extracted_terms": len(extracted_list),
            "data_sources": ["seed_dictionary", "wikipedia", "mit_ocw", "engineering_portals"]
        },
        "terms": sorted(seed_list, key=lambda t: (t["category"], t["en"])),
        "extracted_extras": sorted(extracted_list, key=lambda t: (t["category"], t["en"]))
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2))

    # Generate Markdown
    categories = {}
    for t in output["terms"] + output["extracted_extras"]:
        cat = t["category"]
        categories.setdefault(cat, []).append(t)

    md_lines = [
        "# 机械工程中英术语对照表 V2\n",
        f"> 版本 2.0 | 2026-05-17 | 总计 {len(terminology)} 条术语\n",
        f"> 核心(含中文) {len(seed_list)} 条 + 自动提取 {len(extracted_list)} 条\n",
        "---\n",
    ]

    cat_order = ["core", "工程材料", "力学强度", "机械设计", "制造工艺",
                 "热工流体", "机电自动化", "制图CAD", "标准规范", "未分类"]

    # Show only terms WITH Chinese translations in the main table
    md_lines.append("\n## 核心术语（含中英文）\n")
    md_lines.append("| 英文 | 中文 | 分类 |\n|------|------|------|\n")
    for t in sorted(seed_list, key=lambda x: (x["category"], x["en"])):
        md_lines.append(f"| {t['en']} | {t['zh']} | {t['category']} |\n")

    md_lines.append("\n---\n## 自动提取词条（待补充中文翻译）\n")
    md_lines.append("| 英文 | 来源 | 分类 |\n|------|------|------|\n")
    for t in sorted(extracted_list, key=lambda x: (x["category"], x["en"])):
        src_map = {"wikipedia": "W", "mit_ocw": "M", "engineering_portal": "E"}
        src = src_map.get(t.get("source",""), t.get("source",""))
        md_lines.append(f"| {t['en'][:60]} | {src} | {t['category']} |\n")

    OUTPUT_MD.write_text("".join(md_lines))
    print(f"✅ 术语表V2: {len(seed_list)} 核心 + {len(extracted_list)} 自动提取 = {len(terminology)} 总计", file=sys.stderr)
    print(f"   JSON: {OUTPUT_JSON}", file=sys.stderr)
    print(f"   MD:   {OUTPUT_MD}", file=sys.stderr)

if __name__ == "__main__":
    main()
