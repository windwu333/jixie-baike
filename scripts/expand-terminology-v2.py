#!/usr/bin/env python3
"""
机械师大百科 术语扩展V2 — 从 Wikipedia / efunda / engineers-edge / engineering-toolbox 提取术语
并生成变体条目, 扩展现有术语库 645 -> 5000+ 条。

输出: knowledge-base/mech-terminology-v2.json (保留原有 + 追加新增)
"""

import json
import re
import os
import sys
from collections import Counter

PROJECT_ROOT = "/Users/windwu/Desktop/机械师大百科项目"
TERM_FILE = os.path.join(PROJECT_ROOT, "knowledge-base", "mech-terminology-v2.json")
WIKI_FILE = os.path.join(PROJECT_ROOT, "knowledge-base", "wikipedia-pages.json")
OUTPUT_FILE = TERM_FILE  # Write back in-place

CATEGORY_MAP_WIKI = {
    "Mechanical_engineering": "机械设计",
    "Manufacturing": "制造工艺",
    "Heat_transfer": "热工流体",
    "Machine_elements": "机械设计",
    "Mechanical_design": "机械设计",
    "Fluid_mechanics": "热工流体",
    "Engine_technology": "机电自动化",
    "Industrial_automation": "机电自动化",
    "Finite_element_method": "力学强度",
    "Engineering_materials": "工程材料",
    "Hydraulics": "热工流体",
    "Machining": "制造工艺",
}

# ================================================================
# 大型机械工程英->中 专业字典 (~2200+ entries)
# ================================================================
EN2ZH_DICT = {
    # A
    "abrasion": "磨损",
    "absolute pressure": "绝对压力",
    "absolute temperature": "绝对温度",
    "absolute zero": "绝对零度",
    "absorber": "吸收器",
    "absorption": "吸收",
    "accelerometer": "加速度计",
    "accumulator": "蓄能器",
    "accuracy": "精度",
    "acid": "酸",
    "acme thread": "梯形螺纹",
    "acoustic": "声学的",
    "actuator": "执行器",
    "adapter": "适配器",
    "addendum": "齿顶高",
    "adhesion": "粘附",
    "adiabatic": "绝热的",
    "adjustable": "可调",
    "aerodynamics": "空气动力学",
    "aftercooler": "后冷却器",
    "agitator": "搅拌器",
    "air compressor": "空气压缩机",
    "air conditioner": "空调",
    "air cylinder": "气缸",
    "air filter": "空气过滤器",
    "air hammer": "气锤",
    "air handler": "空气处理机",
    "air motor": "气动马达",
    "air preheater": "空气预热器",
    "air spring": "空气弹簧",
    "airfoil": "翼型",
    "airshaft": "气胀轴",
    "alignment": "对中",
    "alkali": "碱",
    "alloy": "合金",
    "alloy steel": "合金钢",
    "alternator": "交流发电机",
    "aluminum": "铝",
    "aluminum alloy": "铝合金",
    "ammeter": "电流表",
    "amplifier": "放大器",
    "amplitude": "振幅",
    "angle": "角",
    "angle of attack": "攻角",
    "annealing": "退火",
    "anode": "阳极",
    "anodizing": "阳极氧化",
    "anvil": "砧座",
    "apparatus": "装置",
    "arbor": "心轴",
    "arc welding": "电弧焊",
    "assembly": "装配",
    "asymmetric": "不对称",
    "atmosphere": "大气",
    "atmospheric pressure": "大气压",
    "atomic": "原子的",
    "attenuation": "衰减",
    "austenite": "奥氏体",
    "autofrettage": "自紧",
    "automation": "自动化",
    "automaton": "自动机",
    "auxiliary": "辅助",
    "axial": "轴向",
    "axial flow": "轴流",
    "axial load": "轴向载荷",
    "axial piston pump": "轴向柱塞泵",
    "axis": "轴",
    "axle": "车轴",
    # B
    "backdrive": "反向驱动",
    "backlash": "齿隙",
    "baffle": "挡板",
    "balance": "平衡",
    "balancing": "平衡",
    "ball bearing": "球轴承",
    "ball detent": "球定位器",
    "ball screw": "滚珠丝杠",
    "ball valve": "球阀",
    "band brake": "带式制动器",
    "bar": "棒材",
    "barometer": "气压计",
    "barrel": "筒体",
    "base": "基座",
    "base plate": "底板",
    "baseline": "基准线",
    "batch": "批次",
    "battery": "电池",
    "bauxite": "铝土矿",
    "beam": "梁",
    "bearing": "轴承",
    "bed": "床身",
    "bell crank": "直角杠杆",
    "bellows": "波纹管",
    "belt": "皮带",
    "belt conveyor": "皮带输送机",
    "belt drive": "皮带传动",
    "bend": "弯曲",
    "bending": "弯曲",
    "bending moment": "弯矩",
    "bevel gear": "锥齿轮",
    "bevel": "斜面",
    "billet": "钢坯",
    "bimetal": "双金属",
    "binder": "粘结剂",
    "bit": "钻头",
    "blast furnace": "高炉",
    "bleed": "泄放",
    "blend": "混合",
    "blind flange": "盲板法兰",
    "blister": "气泡",
    "block": "块",
    "blow molding": "吹塑",
    "blower": "鼓风机",
    "blueprint": "蓝图",
    "board": "板",
    "body": "本体",
    "boiler": "锅炉",
    "bolt": "螺栓",
    "bond": "结合",
    "bonding": "粘接",
    "bore": "孔",
    "boring": "镗孔",
    "boring machine": "镗床",
    "bottom": "底部",
    "boundary": "边界",
    "boundary condition": "边界条件",
    "boundary layer": "边界层",
    "bracket": "支架",
    "brake": "制动器",
    "braking": "制动",
    "brass": "黄铜",
    "brazing": "钎焊",
    "break": "断裂",
    "breakdown": "故障",
    "breaker": "断路器",
    "brick": "砖",
    "bridge": "桥",
    "brightness": "亮度",
    "brine": "盐水",
    "Brinell hardness": "布氏硬度",
    "brittle": "脆性",
    "brittle fracture": "脆性断裂",
    "broach": "拉刀",
    "broaching": "拉削",
    "bronze": "青铜",
    "brush": "刷",
    "bubble": "气泡",
    "bucket": "铲斗",
    "buckling": "屈曲",
    "buffer": "缓冲器",
    "buffing": "抛光",
    "bulb": "灯泡",
    "bulk": "体",
    "bulk modulus": "体积模量",
    "bulkhead": "隔板",
    "bump": "碰撞",
    "bushing": "衬套",
    "butterfly valve": "蝶阀",
    "butt weld": "对接焊",
    # C
    "cabinet": "机柜",
    "cable": "电缆",
    "cadmium": "镉",
    "cage": "保持架",
    "calcination": "煅烧",
    "calcium": "钙",
    "calibration": "校准",
    "caliper": "卡尺",
    "camber": "弧高",
    "cam": "凸轮",
    "camshaft": "凸轮轴",
    "canopy": "罩",
    "cantilever": "悬臂梁",
    "capacitor": "电容器",
    "capacity": "容量",
    "capillary": "毛细管",
    "capstan": "绞盘",
    "capsule": "胶囊",
    "carbide": "硬质合金",
    "carbon": "碳",
    "carbon steel": "碳钢",
    "carburetor": "化油器",
    "carcass": "骨架",
    "carrier": "托架",
    "cartridge": "筒",
    "case hardening": "表面硬化",
    "casing": "壳体",
    "cassette": "盒",
    "cast": "铸造",
    "cast iron": "铸铁",
    "casting": "铸件",
    "catalyst": "催化剂",
    "catheter": "导管",
    "cathode": "阴极",
    "cavitation": "空化",
    "cavity": "型腔",
    "cell": "单元",
    "cement": "水泥",
    "center": "中心",
    "centrifuge": "离心机",
    "centrifugal": "离心",
    "centrifugal compressor": "离心压缩机",
    "centrifugal pump": "离心泵",
    "ceramic": "陶瓷",
    "chain": "链条",
    "chain drive": "链传动",
    "chamber": "腔室",
    "chamfer": "倒角",
    "channel": "槽钢",
    "characteristic": "特性",
    "charge": "充",
    "check valve": "止回阀",
    "chemical": "化学",
    "chiller": "冷水机",
    "chip": "切屑",
    "chloride": "氯化物",
    "chuck": "卡盘",
    "chute": "溜槽",
    "circle": "圆",
    "circuit": "电路",
    "circuit breaker": "断路器",
    "circular": "圆形",
    "circular pitch": "周节",
    "circulation": "循环",
    "cladding": "包层",
    "clamp": "夹具",
    "clamping": "夹紧",
    "clasp": "扣",
    "classification": "分类",
    "claw": "爪",
    "cleaner": "清洗机",
    "clearance": "间隙",
    "cleat": "楔子",
    "clinch": "铆接",
    "clock": "时钟",
    "clockwise": "顺时针",
    "clone": "克隆",
    "closed loop": "闭环",
    "clutch": "离合器",
    "coating": "涂层",
    "coaxial": "同轴",
    "cock": "旋塞",
    "coefficient": "系数",
    "coil": "线圈",
    "cold forming": "冷成形",
    "cold working": "冷加工",
    "collar": "轴环",
    "collector": "收集器",
    "collet": "弹簧夹头",
    "column": "柱",
    "combustion": "燃烧",
    "combustion chamber": "燃烧室",
    "communication": "通信",
    "commutator": "换向器",
    "compact": "紧凑",
    "compaction": "压实",
    "compatibility": "兼容性",
    "complex": "复杂",
    "component": "部件",
    "composite": "复合材料",
    "compound": "复合",
    "compress": "压缩",
    "compression": "压缩",
    "compression molding": "压缩成型",
    "compression spring": "压缩弹簧",
    "compressive strength": "抗压强度",
    "compressor": "压缩机",
    "computation": "计算",
    "computer": "计算机",
    "concentrate": "浓缩",
    "concentric": "同心",
    "concrete": "混凝土",
    "condensation": "冷凝",
    "condenser": "冷凝器",
    "condition": "条件",
    "conditioning": "调节",
    "conductance": "电导",
    "conduction": "传导",
    "conductivity": "电导率",
    "conductor": "导体",
    "conduit": "导管",
    "cone": "锥体",
    "configuration": "配置",
    "confining": "约束",
    "conical": "圆锥",
    "connect": "连接",
    "connecting rod": "连杆",
    "connection": "连接",
    "connector": "连接器",
    "conservation": "守恒",
    "consistency": "一致性",
    "constant": "常数",
    "constraint": "约束",
    "construction": "结构",
    "consumable": "消耗品",
    "contact": "接触",
    "container": "容器",
    "contaminant": "污染物",
    "contamination": "污染",
    "continuity": "连续性",
    "continuous": "连续",
    "contour": "轮廓",
    "contract": "收缩",
    "control": "控制",
    "control valve": "控制阀",
    "controller": "控制器",
    "convection": "对流",
    "convergence": "收敛",
    "conversion": "转换",
    "converter": "转换器",
    "conveyor": "输送机",
    "coolant": "冷却液",
    "cooler": "冷却器",
    "cooling": "冷却",
    "cooling tower": "冷却塔",
    "coordinate": "坐标",
    "copper": "铜",
    "cord": "绳",
    "core": "芯",
    "corner": "角",
    "corrosion": "腐蚀",
    "corrugated": "波纹",
    "counter": "计数器",
    "counterbore": "沉孔",
    "countersink": "锥形沉孔",
    "couple": "力偶",
    "coupling": "联轴器",
    "crack": "裂纹",
    "cradle": "支架",
    "crane": "起重机",
    "crankshaft": "曲轴",
    "creep": "蠕变",
    "critical": "临界",
    "cross": "十字",
    "crosshead": "十字头",
    "cryogenic": "低温",
    "crystal": "晶体",
    "crystalline": "结晶",
    "cube": "立方体",
    "cubic": "立方",
    "cure": "固化",
    "curing": "固化",
    "current": "电流",
    "curvature": "曲率",
    "curve": "曲线",
    "cushion": "缓冲",
    "cut-off": "切断",
    "cutting": "切削",
    "cutting fluid": "切削液",
    "cutting tool": "刀具",
    "cycle": "循环",
    "cyclic": "循环",
    "cyclone": "旋风分离器",
    "cylinder": "气缸",
    "cylindrical": "圆柱",
    # D
    "damage": "损伤",
    "damper": "阻尼器",
    "damping": "阻尼",
    "data": "数据",
    "dead load": "静载荷",
    "debris": "碎屑",
    "decay": "衰减",
    "deck": "甲板",
    "decomposition": "分解",
    "decontamination": "净化",
    "defect": "缺陷",
    "deflection": "挠度",
    "deformation": "变形",
    "degreasing": "脱脂",
    "degree": "度",
    "delay": "延迟",
    "density": "密度",
    "deoxidation": "脱氧",
    "deposit": "沉积",
    "deposition": "沉积",
    "depreciation": "折旧",
    "depth": "深度",
    "derivative": "导数",
    "desalination": "脱盐",
    "desiccant": "干燥剂",
    "design": "设计",
    "destruction": "破坏",
    "detection": "检测",
    "detector": "检测器",
    "detent": "定位器",
    "deviation": "偏差",
    "device": "装置",
    "dewatering": "脱水",
    "diagnosis": "诊断",
    "diagram": "图",
    "diameter": "直径",
    "diamond": "金刚石",
    "diaphragm": "隔膜",
    "die": "模具",
    "die casting": "压铸",
    "dielectric": "介电",
    "diesel": "柴油",
    "differential": "差动",
    "diffuser": "扩散器",
    "diffusion": "扩散",
    "digit": "数字",
    "digital": "数字",
    "dilatation": "膨胀",
    "dimension": "尺寸",
    "diode": "二极管",
    "direct current": "直流",
    "direction": "方向",
    "discharge": "排放",
    "disconnect": "断开",
    "displacement": "位移",
    "dissipation": "耗散",
    "distance": "距离",
    "distillation": "蒸馏",
    "distortion": "畸变",
    "distribution": "分布",
    "distributor": "分配器",
    "diverter": "转向器",
    "dog": "挡块",
    "dome": "穹顶",
    "door": "门",
    "dosing": "计量",
    "double": "双",
    "dowel": "定位销",
    "downcomer": "下降管",
    "draft": "草案",
    "drafting": "制图",
    "drag": "阻力",
    "drain": "排水",
    "drawing": "拉深",
    "dressing": "修整",
    "drift": "漂移",
    "drill": "钻头",
    "drilling": "钻孔",
    "drilling machine": "钻床",
    "drive": "驱动",
    "drive shaft": "驱动轴",
    "driver": "驱动器",
    "drop": "压降",
    "drum": "鼓",
    "dryer": "干燥器",
    "drying": "干燥",
    "duct": "管道",
    "ductile": "韧性",
    "ductility": "延展性",
    "dummy": "盲",
    "dump": "排放",
    "duplex": "双相",
    "durability": "耐久性",
    "dust": "粉尘",
    "dwell": "停留",
    "dynamo": "发电机",
    "dynamometer": "测力计",
    # E
    "eccentric": "偏心",
    "eccentricity": "偏心度",
    "economizer": "省煤器",
    "edge": "边缘",
    "efficiency": "效率",
    "effluent": "流出物",
    "elastic": "弹性",
    "elasticity": "弹性",
    "elastomer": "弹性体",
    "electric": "电",
    "electric motor": "电动机",
    "electrical": "电气",
    "electricity": "电",
    "electrode": "电极",
    "electrolysis": "电解",
    "electrolyte": "电解质",
    "electromagnet": "电磁铁",
    "electron": "电子",
    "electronic": "电子",
    "electroplate": "电镀",
    "elevation": "标高",
    "elevator": "电梯",
    "elongation": "伸长率",
    "emission": "排放",
    "emissivity": "发射率",
    "energy": "能量",
    "engine": "发动机",
    "engineering": "工程",
    "enthalpy": "焓",
    "entropy": "熵",
    "envelope": "包络",
    "environment": "环境",
    "epicyclic": "周转",
    "equation": "方程",
    "equilibrium": "平衡",
    "equipment": "设备",
    "equivalent": "等效",
    "erosion": "侵蚀",
    "error": "误差",
    "etching": "蚀刻",
    "evacuation": "抽空",
    "evaluation": "评估",
    "evaporation": "蒸发",
    "evaporator": "蒸发器",
    "examination": "检验",
    "exchanger": "交换器",
    "excitation": "励磁",
    "exhaust": "排气",
    "exhaust valve": "排气阀",
    "expansion": "膨胀",
    "expansion joint": "膨胀节",
    "experiment": "实验",
    "explosion": "爆炸",
    "exposure": "暴露",
    "extension": "延伸",
    "extraction": "萃取",
    "extruder": "挤出机",
    "extrusion": "挤压",
    "eye": "眼",
    "eyebolt": "吊环螺栓",
    # F
    "fabric": "织物",
    "fabrication": "制造",
    "face": "面",
    "face seal": "端面密封",
    "failure": "失效",
    "fan": "风扇",
    "fatigue": "疲劳",
    "fatigue strength": "疲劳强度",
    "feed": "进给",
    "feedback": "反馈",
    "feeder": "给料机",
    "feeding": "进给",
    "ferrite": "铁素体",
    "ferrous": "含铁",
    "fiber": "纤维",
    "fiber optic": "光纤",
    "field": "场",
    "filament": "灯丝",
    "file": "锉刀",
    "fill": "填充",
    "filler": "填充物",
    "fillet": "圆角",
    "film": "膜",
    "filter": "过滤器",
    "filtration": "过滤",
    "fin": "翅片",
    "final": "最终",
    "finish": "精加工",
    "finishing": "精加工",
    "finite element": "有限元",
    "finishing": "精加工",
    "fire": "火",
    "fireproof": "防火",
    "firmware": "固件",
    "fitting": "管件",
    "fixture": "夹具",
    "flame": "火焰",
    "flame cutting": "火焰切割",
    "flame hardening": "火焰淬火",
    "flange": "法兰",
    "flapper": "挡板",
    "flash": "闪光",
    "flask": "砂箱",
    "flat": "平",
    "flatness": "平面度",
    "flex": "弯曲",
    "flexibility": "柔性",
    "flexible": "柔性",
    "flexure": "挠曲",
    "float": "浮子",
    "floatation": "浮选",
    "floating": "浮动",
    "flood": "溢流",
    "floor": "地面",
    "flow": "流量",
    "flow control": "流量控制",
    "flow meter": "流量计",
    "flow rate": "流速",
    "fluid": "流体",
    "fluid coupling": "液力耦合器",
    "fluidics": "射流",
    "fluorescence": "荧光",
    "fluoride": "氟化物",
    "flush": "冲洗",
    "flux": "通量",
    "flywheel": "飞轮",
    "foam": "泡沫",
    "foil": "箔",
    "fold": "折叠",
    "force": "力",
    "forced convection": "强制对流",
    "forging": "锻造",
    "fork": "叉",
    "form": "形式",
    "form grinding": "成形磨削",
    "forming": "成形",
    "formula": "公式",
    "foundation": "基础",
    "foundry": "铸造厂",
    "fracture": "断裂",
    "frame": "框架",
    "free": "自由",
    "free convection": "自然对流",
    "frequency": "频率",
    "friction": "摩擦",
    "front": "前",
    "fuel": "燃料",
    "fuel cell": "燃料电池",
    "fuel injection": "燃油喷射",
    "fume": "烟雾",
    "function": "功能",
    "furnace": "炉",
    "fuse": "保险丝",
    "fusion": "熔化",
    # G
    "gage": "量规",
    "gallery": "通道",
    "galvanic": "电偶",
    "galvanize": "镀锌",
    "galvanometer": "检流计",
    "gamma": "伽马",
    "gap": "间隙",
    "gas": "气体",
    "gas turbine": "燃气轮机",
    "gasket": "垫片",
    "gasoline": "汽油",
    "gate": "闸门",
    "gauge": "仪表",
    "gear": "齿轮",
    "gear box": "齿轮箱",
    "gear cutting": "齿轮加工",
    "gear pump": "齿轮泵",
    "gear train": "齿轮系",
    "generator": "发电机",
    "glass": "玻璃",
    "globe valve": "截止阀",
    "glow": "辉光",
    "governor": "调速器",
    "grade": "等级",
    "gradient": "梯度",
    "grain": "晶粒",
    "graphite": "石墨",
    "gravity": "重力",
    "grease": "润滑脂",
    "grid": "网格",
    "grinder": "磨床",
    "grinding": "磨削",
    "gripper": "夹爪",
    "groove": "沟槽",
    "ground": "接地",
    "guard": "防护罩",
    "guide": "导向",
    "gutter": "槽",
    "gyroscope": "陀螺仪",
    # H
    "hair": "毛发",
    "half": "半",
    "hammer": "锤",
    "hand": "手",
    "handrail": "扶手",
    "hanger": "吊架",
    "hard chrome": "硬铬",
    "hard metal": "硬质合金",
    "hardboard": "硬板",
    "harden": "硬化",
    "hardener": "硬化剂",
    "hardness": "硬度",
    "hardware": "硬件",
    "hatch": "舱口",
    "hazard": "危险",
    "head": "头",
    "head loss": "水头损失",
    "header": "集管",
    "heat": "热",
    "heat capacity": "热容",
    "heat engine": "热机",
    "heat exchanger": "换热器",
    "heat pump": "热泵",
    "heat recovery": "热回收",
    "heat transfer": "传热",
    "heat treatment": "热处理",
    "heater": "加热器",
    "heating": "加热",
    "heavy": "重",
    "height": "高度",
    "helical": "螺旋",
    "helical gear": "斜齿轮",
    "helix": "螺旋线",
    "hemisphere": "半球",
    "hermetic": "密封",
    "high pressure": "高压",
    "hinge": "铰链",
    "hobbing": "滚齿",
    "holder": "支架",
    "hollow": "空心",
    "holography": "全息术",
    "honeycomb": "蜂窝",
    "hood": "罩",
    "hook": "钩",
    "hopper": "料斗",
    "horizontal": "水平",
    "hose": "软管",
    "housing": "壳体",
    "hub": "轮毂",
    "humidifier": "加湿器",
    "humidity": "湿度",
    "hybrid": "混合",
    "hydrant": "消防栓",
    "hydraulic": "液压",
    "hydraulic cylinder": "液压缸",
    "hydraulic motor": "液压马达",
    "hydraulic press": "液压机",
    "hydraulics": "水力学",
    "hydrocarbon": "碳氢化合物",
    "hydrodynamics": "流体动力学",
    "hydrofoil": "水翼",
    "hydrogen": "氢",
    "hydrolysis": "水解",
    "hydrometer": "比重计",
    "hydrostatic": "静水压",
    "hygrometer": "湿度计",
    "hysteresis": "滞后",
    # I
    "ice": "冰",
    "idle": "怠速",
    "idler": "惰轮",
    "ignition": "点火",
    "image": "图像",
    "immersion": "浸入",
    "impact": "冲击",
    "impedance": "阻抗",
    "impeller": "叶轮",
    "impulse": "冲量",
    "inclusion": "夹杂物",
    "index": "索引",
    "indication": "指示",
    "indicator": "指示器",
    "induction": "感应",
    "induction motor": "感应电动机",
    "inductor": "电感器",
    "industrial": "工业",
    "inertia": "惯性",
    "inertial": "惯性",
    "inflation": "充气",
    "infrared": "红外",
    "ingot": "锭",
    "injection": "注射",
    "injection molding": "注塑成型",
    "inlet": "入口",
    "inner": "内",
    "input": "输入",
    "insert": "嵌入件",
    "inspection": "检验",
    "installation": "安装",
    "instrument": "仪器",
    "instrumentation": "仪表",
    "insulation": "绝缘",
    "insulator": "绝缘体",
    "intake": "进气",
    "integral": "积分",
    "integration": "集成",
    "intensity": "强度",
    "interface": "界面",
    "interference": "干涉",
    "interlock": "互锁",
    "intermediate": "中间",
    "internal": "内部",
    "internal combustion": "内燃",
    "inverter": "逆变器",
    "investment casting": "熔模铸造",
    "ion": "离子",
    "iron": "铁",
    "irradiation": "辐照",
    "isolation": "隔离",
    "isothermal": "等温",
    # J
    "jack": "千斤顶",
    "jacket": "夹套",
    "jacking": "顶升",
    "jaw": "颚",
    "jet": "射流",
    "jig": "钻模",
    "jog": "点动",
    "join": "连接",
    "joint": "接头",
    "journal": "轴颈",
    "junction": "接合",
    # K
    "key": "键",
    "keyway": "键槽",
    "kiln": "窑",
    "kinematics": "运动学",
    "kinetic energy": "动能",
    "knife": "刀",
    "knob": "旋钮",
    "knot": "结",
    # L
    "label": "标签",
    "laboratory": "实验室",
    "labyrinth": "迷宫",
    "lacquer": "漆",
    "ladder": "梯子",
    "lagging": "保温",
    "laminate": "层压",
    "lamination": "层压",
    "lamp": "灯",
    "land": "陆",
    "lapping": "研磨",
    "laser": "激光",
    "laser cutting": "激光切割",
    "laser welding": "激光焊接",
    "latch": "门闩",
    "latent heat": "潜热",
    "lateral": "横向",
    "lathe": "车床",
    "lattice": "晶格",
    "layer": "层",
    "layout": "布局",
    "lead": "铅",
    "lead screw": "丝杠",
    "leak": "泄漏",
    "leakage": "泄漏",
    "length": "长度",
    "lens": "透镜",
    "lever": "杠杆",
    "life": "寿命",
    "lift": "升降机",
    "ligament": "韧带",
    "light": "光",
    "lightning": "闪电",
    "limit": "极限",
    "limiter": "限位器",
    "line": "线",
    "linear": "线性",
    "liner": "衬里",
    "link": "连杆",
    "linkage": "连杆机构",
    "liquid": "液体",
    "lithium": "锂",
    "live load": "活载荷",
    "load": "载荷",
    "loader": "装载机",
    "loam": "壤土",
    "lock": "锁",
    "lock washer": "锁紧垫圈",
    "locking": "锁紧",
    "locomotive": "机车",
    "locus": "轨迹",
    "log": "日志",
    "longitudinal": "纵向",
    "loop": "回路",
    "loose": "松散",
    "loss": "损失",
    "louver": "百叶窗",
    "low pressure": "低压",
    "lube": "润滑",
    "lubricant": "润滑剂",
    "lubrication": "润滑",
    "lug": "凸耳",
    "lumber": "木材",
    "lumen": "流明",
    "luminance": "亮度",
    "lump": "块",
    # M
    "machine": "机器",
    "machine element": "机械零件",
    "machine tool": "机床",
    "machinery": "机械",
    "machining": "机加工",
    "magnesium": "镁",
    "magnet": "磁铁",
    "magnetic": "磁性",
    "magnetism": "磁性",
    "magnetron": "磁控管",
    "maintenance": "维护",
    "manifold": "歧管",
    "manometer": "压力计",
    "manpower": "人力",
    "manual": "手动",
    "manufacturing": "制造",
    "maraging": "马氏体时效",
    "marble": "大理石",
    "margin": "裕度",
    "marine": "船舶",
    "mark": "标记",
    "marking": "标记",
    "martensite": "马氏体",
    "mass": "质量",
    "master": "主",
    "master cylinder": "主缸",
    "mastic": "玛蹄脂",
    "mat": "垫",
    "material": "材料",
    "matrix": "矩阵",
    "measurement": "测量",
    "measuring": "测量",
    "mechanical": "机械",
    "mechanical seal": "机械密封",
    "mechanics": "力学",
    "mechanism": "机构",
    "medium": "介质",
    "melt": "熔化",
    "melting": "熔化",
    "membrane": "膜",
    "mercury": "汞",
    "mesh": "网格",
    "metal": "金属",
    "metal cutting": "金属切削",
    "metal forming": "金属成形",
    "metallurgy": "冶金学",
    "meter": "米",
    "method": "方法",
    "mica": "云母",
    "microprocessor": "微处理器",
    "microscope": "显微镜",
    "microstructure": "显微组织",
    "microwave": "微波",
    "milling": "铣削",
    "milling machine": "铣床",
    "mineral": "矿物",
    "miniature": "微型",
    "minimum": "最小",
    "mining": "采矿",
    "mirror": "反射镜",
    "mixer": "混合器",
    "mixing": "混合",
    "mixture": "混合物",
    "mobile": "移动",
    "mode": "模式",
    "model": "模型",
    "modulus": "模量",
    "moisture": "水分",
    "mold": "模具",
    "molding": "成型",
    "molecular": "分子",
    "molecule": "分子",
    "molten": "熔融",
    "molybdenum": "钼",
    "moment": "力矩",
    "momentum": "动量",
    "monitor": "监控",
    "monitoring": "监控",
    "monoblock": "整体",
    "mortar": "砂浆",
    "motion": "运动",
    "motor": "电机",
    "mount": "安装",
    "mounting": "底座",
    "movement": "移动",
    "muffler": "消声器",
    "multimeter": "万用表",
    "multi-stage": "多级",
    "mutation": "突变",
    # N
    "nail": "钉子",
    "natural": "自然",
    "natural convection": "自然对流",
    "natural frequency": "固有频率",
    "navigation": "导航",
    "neck": "颈部",
    "needle": "针",
    "needle valve": "针形阀",
    "negative": "负",
    "network": "网络",
    "neutral": "中性",
    "neutral axis": "中性轴",
    "nickel": "镍",
    "nip": "压区",
    "nitride": "氮化物",
    "nitriding": "渗氮",
    "nitrogen": "氮",
    "noise": "噪声",
    "no-load": "空载",
    "nominal": "标称",
    "non-destructive": "无损",
    "non-ferrous": "有色",
    "non-metal": "非金属",
    "nozzle": "喷嘴",
    "nuclear": "核",
    "number": "编号",
    "nut": "螺母",
    "nylon": "尼龙",
    # O
    "object": "物体",
    "observation": "观察",
    "obturator": "堵塞器",
    "occupation": "职业",
    "oil": "油",
    "oil seal": "油封",
    "oil pump": "油泵",
    "opacity": "不透明度",
    "opening": "开口",
    "operating": "操作",
    "operation": "操作",
    "operator": "操作员",
    "optic": "光学",
    "optical": "光学",
    "optimization": "优化",
    "orange": "橙",
    "orbit": "轨道",
    "order": "顺序",
    "ore": "矿石",
    "orifice": "孔口",
    "oscillation": "振荡",
    "oscillator": "振荡器",
    "osmosis": "渗透",
    "outlet": "出口",
    "output": "输出",
    "oval": "椭圆",
    "oven": "烘箱",
    "overall": "总体",
    "overhaul": "大修",
    "overheat": "过热",
    "overload": "过载",
    "overspeed": "超速",
    "oxide": "氧化物",
    "oxidizer": "氧化剂",
    "oxygen": "氧气",
    "ozone": "臭氧",
    # P
    "pack": "包",
    "package": "包装",
    "packing": "填料",
    "pad": "垫",
    "paint": "涂料",
    "painting": "涂装",
    "pair": "对",
    "palladium": "钯",
    "pan": "盘",
    "panel": "面板",
    "paper": "纸",
    "parabolic": "抛物线",
    "parallel": "平行",
    "parameter": "参数",
    "part": "零件",
    "particle": "粒子",
    "partition": "隔板",
    "pass": "通道",
    "passivation": "钝化",
    "paste": "糊",
    "patch": "补丁",
    "patent": "专利",
    "path": "路径",
    "pattern": "图案",
    "peak": "峰值",
    "pearlite": "珠光体",
    "pedestal": "底座",
    "peel": "剥离",
    "pendulum": "摆",
    "penetration": "穿透",
    "perforation": "穿孔",
    "performance": "性能",
    "perimeter": "周长",
    "period": "周期",
    "permanent": "永久",
    "permeability": "渗透率",
    "permit": "许可",
    "perpendicular": "垂直",
    "personal": "个人",
    "petrol": "汽油",
    "petroleum": "石油",
    "phase": "相",
    "phenolic": "酚醛",
    "phonon": "声子",
    "phosphate": "磷酸盐",
    "phosphor": "磷",
    "phosphorus": "磷",
    "photocell": "光电池",
    "photoelectric": "光电",
    "photography": "摄影",
    "photometer": "光度计",
    "physic": "物理",
    "pickling": "酸洗",
    "pickup": "拾取",
    "piece": "件",
    "piezoelectric": "压电",
    "pig": "生铁",
    "pile": "桩",
    "pilot": "先导",
    "pilot valve": "先导阀",
    "pin": "销",
    "pinion": "小齿轮",
    "pipe": "管道",
    "pipe fitting": "管件",
    "pipeline": "管线",
    "piping": "管道",
    "piston": "活塞",
    "piston pump": "活塞泵",
    "piston ring": "活塞环",
    "pit": "坑",
    "pitch": "螺距",
    "pivot": "枢轴",
    "plain bearing": "滑动轴承",
    "plane": "平面",
    "planet": "行星",
    "planetary": "行星",
    "planetary gear": "行星齿轮",
    "planing": "刨削",
    "plasma": "等离子",
    "plasma cutting": "等离子切割",
    "plastic": "塑料",
    "plastic deformation": "塑性变形",
    "plasticity": "塑性",
    "plate": "板",
    "platform": "平台",
    "plating": "电镀",
    "platinum": "铂",
    "play": "游隙",
    "plenum": "充气室",
    "plier": "钳子",
    "plot": "绘图",
    "plug": "插头",
    "plumb": "铅锤",
    "plumbing": "管道",
    "plunger": "柱塞",
    "plywood": "胶合板",
    "pneumatic": "气动",
    "pneumatics": "气动学",
    "pocket": "袋",
    "point": "点",
    "poise": "泊",
    "poison": "毒",
    "polar": "极",
    "polarization": "极化",
    "polish": "抛光",
    "polishing": "抛光",
    "pollution": "污染",
    "polyamide": "聚酰胺",
    "polycarbonate": "聚碳酸酯",
    "polyester": "聚酯",
    "polyethylene": "聚乙烯",
    "polymer": "聚合物",
    "polypropylene": "聚丙烯",
    "polystyrene": "聚苯乙烯",
    "polyurethane": "聚氨酯",
    "polyvinyl": "聚乙烯基",
    "pool": "池",
    "porosity": "孔隙率",
    "porous": "多孔",
    "port": "口",
    "position": "位置",
    "positioner": "定位器",
    "positive": "正",
    "positive displacement": "容积",
    "post": "柱",
    "pot": "罐",
    "potential": "势",
    "potential energy": "势能",
    "potentiometer": "电位计",
    "powder": "粉末",
    "powder metallurgy": "粉末冶金",
    "power": "功率",
    "power plant": "发电厂",
    "power transmission": "动力传输",
    "precipitation": "沉淀",
    "precision": "精密",
    "preheater": "预热器",
    "preload": "预载荷",
    "press": "压力机",
    "press brake": "折弯机",
    "pressure": "压力",
    "pressure drop": "压降",
    "pressure gauge": "压力表",
    "pressure regulator": "调压阀",
    "pressure relief": "泄压",
    "pressure vessel": "压力容器",
    "pressurization": "加压",
    "pre-stress": "预应力",
    "priming": "引水",
    "printer": "打印机",
    "prism": "棱镜",
    "probability": "概率",
    "probe": "探头",
    "procedure": "程序",
    "process": "工艺",
    "processing": "加工",
    "processor": "处理器",
    "producer": "生产者",
    "product": "产品",
    "production": "生产",
    "profile": "轮廓",
    "program": "程序",
    "programmable": "可编程",
    "projection": "投影",
    "propagation": "传播",
    "propeller": "螺旋桨",
    "property": "性能",
    "proportion": "比例",
    "protection": "保护",
    "protective": "防护",
    "prototype": "原型",
    "pulley": "滑轮",
    "pulp": "纸浆",
    "pulsation": "脉动",
    "pulse": "脉冲",
    "pump": "泵",
    "punch": "冲头",
    "punching": "冲压",
    "purge": "吹扫",
    "purification": "净化",
    "push": "推",
    "pyrometer": "高温计",
    # Q
    "quadrant": "象限",
    "qualification": "合格",
    "quality": "质量",
    "quantity": "数量",
    "quarry": "采石场",
    "quarter": "四分之一",
    "quartz": "石英",
    "quench": "淬火",
    "quenching": "淬火",
    # R
    "rack": "齿条",
    "radar": "雷达",
    "radial": "径向",
    "radial load": "径向载荷",
    "radian": "弧度",
    "radiation": "辐射",
    "radiator": "散热器",
    "radio": "无线电",
    "radius": "半径",
    "rake": "前角",
    "ram": "滑块",
    "random": "随机",
    "range": "范围",
    "rapid prototyping": "快速原型",
    "ratchet": "棘轮",
    "rate": "比率",
    "rating": "额定",
    "ratio": "比",
    "raw material": "原材料",
    "reactance": "电抗",
    "reaction": "反应",
    "reactor": "反应器",
    "reamer": "铰刀",
    "reaming": "铰孔",
    "receiver": "接收器",
    "receptacle": "容器",
    "recession": "衰退",
    "reciprocating": "往复",
    "reclaimer": "取料机",
    "recorder": "记录仪",
    "recovery": "回收",
    "rectifier": "整流器",
    "recycle": "回收",
    "reducer": "减速器",
    "reduction": "减少",
    "redundancy": "冗余",
    "reel": "卷盘",
    "refinery": "精炼厂",
    "refining": "精炼",
    "reflector": "反射器",
    "reflow": "回流",
    "refractory": "耐火",
    "refrigerant": "制冷剂",
    "refrigeration": "制冷",
    "refrigerator": "冰箱",
    "regeneration": "再生",
    "regenerator": "回热器",
    "regulator": "调节器",
    "reinforcement": "增强",
    "relative": "相对",
    "relaxation": "松弛",
    "relay": "继电器",
    "release": "释放",
    "reliability": "可靠性",
    "relief": "泄压",
    "relief valve": "泄压阀",
    "remote": "远程",
    "renewable": "可再生",
    "repair": "修理",
    "repeatability": "重复性",
    "reproduction": "复制",
    "research": "研究",
    "reservoir": "储罐",
    "residual": "残余",
    "residue": "残留",
    "resilience": "回弹",
    "resin": "树脂",
    "resistance": "阻力",
    "resistivity": "电阻率",
    "resistor": "电阻器",
    "resolution": "分辨率",
    "resonance": "共振",
    "resource": "资源",
    "response": "响应",
    "restoration": "修复",
    "restrictor": "节流阀",
    "result": "结果",
    "retaining ring": "卡环",
    "retarder": "减速器",
    "retort": "蒸馏罐",
    "return": "返回",
    "reverberation": "混响",
    "reverse": "反向",
    "revolution": "旋转",
    "revolve": "旋转",
    "rheology": "流变学",
    "rib": "肋",
    "ridge": "脊",
    "rig": "钻机",
    "right angle": "直角",
    "rigid": "刚性",
    "rigidity": "刚度",
    "rim": "轮缘",
    "ring": "环",
    "rinse": "漂洗",
    "ripple": "波纹",
    "rivet": "铆钉",
    "riveting": "铆接",
    "road": "道路",
    "robot": "机器人",
    "robotics": "机器人学",
    "rock": "岩石",
    "rocket": "火箭",
    "rod": "杆",
    "roll": "辊",
    "roller": "滚子",
    "roller bearing": "滚子轴承",
    "rolling": "轧制",
    "roof": "屋顶",
    "room": "房间",
    "root": "根部",
    "rope": "绳索",
    "rotameter": "转子流量计",
    "rotary": "旋转",
    "rotary pump": "旋转泵",
    "rotating": "旋转",
    "rotation": "旋转",
    "rotor": "转子",
    "roughness": "粗糙度",
    "round": "圆",
    "rubber": "橡胶",
    "rule": "规则",
    "runner": "叶轮",
    "rupture": "破裂",
    # S
    "saddle": "鞍座",
    "safe": "安全",
    "safety": "安全",
    "safety valve": "安全阀",
    "sag": "下垂",
    "salt": "盐",
    "sample": "样本",
    "sampling": "采样",
    "sand": "砂",
    "sand blasting": "喷砂",
    "sand casting": "砂型铸造",
    "satellite": "卫星",
    "saturated": "饱和",
    "saw": "锯",
    "sawing": "锯削",
    "scale": "比例",
    "scanner": "扫描仪",
    "scatter": "散射",
    "scavenging": "扫气",
    "schedule": "进度",
    "schematic": "示意图",
    "science": "科学",
    "scoop": "勺",
    "scratch": "划痕",
    "screen": "筛网",
    "screening": "筛选",
    "screw": "螺钉",
    "screw compressor": "螺杆压缩机",
    "screw conveyor": "螺旋输送机",
    "screw pump": "螺杆泵",
    "scrap": "废料",
    "scraper": "刮刀",
    "scrubber": "洗涤器",
    "seal": "密封",
    "sealing": "密封",
    "seam": "接缝",
    "seamless": "无缝",
    "seat": "阀座",
    "section": "截面",
    "sector": "扇形",
    "sediment": "沉积物",
    "seepage": "渗漏",
    "segment": "段",
    "seismic": "地震",
    "selector": "选择器",
    "self": "自",
    "self-locking": "自锁",
    "semi": "半",
    "semiconductor": "半导体",
    "sensor": "传感器",
    "separation": "分离",
    "separator": "分离器",
    "sequence": "顺序",
    "series": "系列",
    "service": "服务",
    "servo": "伺服",
    "servo motor": "伺服电机",
    "servomechanism": "伺服机构",
    "set": "组",
    "set point": "设定点",
    "set screw": "紧定螺钉",
    "settling": "沉降",
    "sewer": "下水道",
    "shaft": "轴",
    "shaft seal": "轴封",
    "shaker": "振动器",
    "shank": "刀柄",
    "shape": "形状",
    "shaping": "成形",
    "sharp": "尖锐",
    "shear": "剪切",
    "shear force": "剪力",
    "shear modulus": "剪切模量",
    "shear stress": "剪应力",
    "sheath": "护套",
    "sheet": "薄板",
    "sheet metal": "钣金",
    "shelf": "架子",
    "shell": "壳体",
    "shield": "屏蔽",
    "shielding": "屏蔽",
    "shift": "移位",
    "shim": "垫片",
    "shock": "冲击",
    "shock absorber": "减震器",
    "shoe": "鞋",
    "shop": "车间",
    "short": "短",
    "short circuit": "短路",
    "shoulder": "肩",
    "shredder": "破碎机",
    "shrink": "收缩",
    "shrinkage": "收缩",
    "shroud": "护罩",
    "shunt": "分流",
    "shut-off": "关闭",
    "shutter": "百叶窗",
    "side": "侧",
    "sieve": "筛",
    "sight": "观察",
    "sight glass": "视镜",
    "signal": "信号",
    "silencer": "消音器",
    "silica": "二氧化硅",
    "silicon": "硅",
    "silver": "银",
    "simulation": "仿真",
    "sine": "正弦",
    "single": "单",
    "sink": "散热器",
    "sintering": "烧结",
    "siphon": "虹吸",
    "site": "现场",
    "size": "尺寸",
    "sketch": "草图",
    "skid": "撬装",
    "skin": "表皮",
    "skip": "跳跃",
    "slag": "炉渣",
    "slave": "从动",
    "sleeve": "套筒",
    "slice": "切片",
    "slide": "滑",
    "slider": "滑块",
    "sliding": "滑动",
    "slip": "滑移",
    "slippage": "滑移",
    "slit": "狭缝",
    "slope": "斜率",
    "slot": "槽",
    "slow": "慢",
    "sludge": "污泥",
    "sluice": "水闸",
    "slurry": "浆料",
    "smoke": "烟",
    "smooth": "光滑",
    "snap": "卡扣",
    "snap ring": "卡环",
    "socket": "插座",
    "soda": "苏打",
    "sodium": "钠",
    "soft": "软",
    "software": "软件",
    "soil": "土壤",
    "solar": "太阳",
    "solar cell": "太阳能电池",
    "solenoid": "电磁阀",
    "solenoid valve": "电磁阀",
    "solid": "固体",
    "solidification": "凝固",
    "solubility": "溶解度",
    "solution": "溶液",
    "solvent": "溶剂",
    "sonic": "声波",
    "soot": "烟灰",
    "sorter": "分选机",
    "sound": "声音",
    "source": "源",
    "space": "空间",
    "spacer": "隔圈",
    "spalling": "剥落",
    "span": "跨度",
    "spare": "备件",
    "spark": "火花",
    "spark plug": "火花塞",
    "spatial": "空间",
    "specification": "规格",
    "specimen": "试样",
    "spectrometer": "光谱仪",
    "spectroscopy": "光谱学",
    "spectrum": "光谱",
    "speed": "速度",
    "speed reducer": "减速器",
    "speedometer": "速度计",
    "spherical": "球面",
    "spindle": "主轴",
    "spiral": "螺旋",
    "splash": "飞溅",
    "splice": "拼接",
    "split": "分体",
    "spoke": "辐条",
    "spool": "阀芯",
    "spot": "点",
    "spot welding": "点焊",
    "spray": "喷雾",
    "spray nozzle": "喷嘴",
    "sprayer": "喷雾器",
    "spring": "弹簧",
    "sprocket": "链轮",
    "sprue": "浇口",
    "spur gear": "直齿轮",
    "square": "方形",
    "squeeze": "挤压",
    "stability": "稳定性",
    "stabilizer": "稳定器",
    "stack": "烟囱",
    "stage": "级",
    "stainless steel": "不锈钢",
    "stamping": "冲压",
    "stand": "架",
    "standard": "标准",
    "standing": "静止",
    "staple": "订书钉",
    "starter": "启动器",
    "starting": "启动",
    "state": "状态",
    "static": "静态",
    "station": "站",
    "statistics": "统计",
    "stator": "定子",
    "stay": "拉杆",
    "steady": "稳态",
    "steam": "蒸汽",
    "steam generator": "蒸汽发生器",
    "steam turbine": "汽轮机",
    "steel": "钢",
    "steelmaking": "炼钢",
    "steering": "转向",
    "stem": "阀杆",
    "step": "步进",
    "step motor": "步进电机",
    "stiffener": "加强筋",
    "stiffness": "刚度",
    "stirrer": "搅拌器",
    "stirring": "搅拌",
    "stitch": "缝合",
    "stock": "库存",
    "stop": "停止",
    "stopper": "止动器",
    "storage": "储存",
    "stove": "炉",
    "strain": "应变",
    "strain gauge": "应变片",
    "strainer": "过滤器",
    "strand": "股",
    "strap": "带",
    "stratification": "分层",
    "stray": "杂散",
    "stream": "流",
    "streamline": "流线",
    "strength": "强度",
    "stress": "应力",
    "stress concentration": "应力集中",
    "stress corrosion": "应力腐蚀",
    "stress relief": "应力消除",
    "stretcher": "拉伸机",
    "striking": "打击",
    "string": "弦",
    "strip": "带材",
    "stroke": "行程",
    "structural": "结构",
    "structure": "结构",
    "strut": "支撑",
    "stud": "螺柱",
    "stud bolt": "螺柱",
    "stuffing box": "填料函",
    "subassembly": "子组件",
    "subcritical": "亚临界",
    "sublimation": "升华",
    "submarine": "潜水艇",
    "submersible": "潜水",
    "substation": "变电站",
    "substitute": "替代",
    "substrate": "基底",
    "suction": "吸入",
    "sump": "集水坑",
    "superalloy": "高温合金",
    "supercharger": "增压器",
    "superconducting": "超导",
    "supercritical": "超临界",
    "superheater": "过热器",
    "supervision": "监督",
    "supply": "供应",
    "support": "支撑",
    "surface": "表面",
    "surface finishing": "表面处理",
    "surface hardening": "表面硬化",
    "surface roughness": "表面粗糙度",
    "surge": "喘振",
    "surge tank": "调压罐",
    "surgery": "外科",
    "surging": "喘振",
    "surplus": "剩余",
    "surrounding": "周围",
    "survey": "测量",
    "suspension": "悬架",
    "swaging": "旋锻",
    "sweat": "汗",
    "sweating": "凝露",
    "sweep": "扫描",
    "swing": "摆动",
    "switch": "开关",
    "switchgear": "开关设备",
    "symbol": "符号",
    "symmetric": "对称",
    "synchronization": "同步",
    "synchronous": "同步",
    "synchrotron": "同步加速器",
    "synthesis": "合成",
    "synthetic": "合成",
    "system": "系统",
    # T
    "table": "工作台",
    "tachometer": "转速表",
    "tack": "粘性",
    "tackle": "滑轮组",
    "tactile": "触觉",
    "tail": "尾",
    "talc": "滑石",
    "tandem": "串联",
    "tangent": "正切",
    "tank": "罐",
    "tap": "丝锥",
    "tape": "带",
    "taper": "锥度",
    "tapping": "攻丝",
    "target": "目标",
    "tariff": "关税",
    "tee": "三通",
    "temperature": "温度",
    "temper": "回火",
    "tempering": "回火",
    "template": "模板",
    "tensile": "拉伸",
    "tensile strength": "抗拉强度",
    "tension": "张力",
    "terminal": "端子",
    "terminology": "术语",
    "terotechnology": "维修技术",
    "test": "试验",
    "tester": "测试仪",
    "testing": "测试",
    "textile": "纺织",
    "thermal": "热",
    "thermal conductivity": "导热系数",
    "thermal expansion": "热膨胀",
    "thermocouple": "热电偶",
    "thermodynamics": "热力学",
    "thermometer": "温度计",
    "thermostat": "恒温器",
    "thickness": "厚度",
    "thin": "薄",
    "thread": "螺纹",
    "thread cutting": "螺纹加工",
    "three-phase": "三相",
    "throat": "喉部",
    "throttle": "节流",
    "thrust": "推力",
    "thrust bearing": "推力轴承",
    "thyristor": "晶闸管",
    "tie": "系杆",
    "tiger": "虎",
    "tight": "紧",
    "tightening": "拧紧",
    "tile": "瓦",
    "tilting": "倾斜",
    "timber": "木材",
    "time": "时间",
    "timer": "定时器",
    "timing": "正时",
    "tin": "锡",
    "tip": "尖端",
    "tire": "轮胎",
    "titanium": "钛",
    "title": "标题",
    "toggle": "肘节",
    "tolerance": "公差",
    "tomography": "断层扫描",
    "tongue": "舌",
    "tool": "工具",
    "tool holder": "刀架",
    "tool steel": "工具钢",
    "tooth": "齿",
    "top": "顶部",
    "torch": "焊炬",
    "torque": "扭矩",
    "torque converter": "变矩器",
    "torsion": "扭转",
    "torsional": "扭转",
    "torus": "环形",
    "total": "总",
    "touch": "触摸",
    "tower": "塔",
    "toxicity": "毒性",
    "trace": "微量",
    "track": "轨道",
    "traction": "牵引",
    "tractor": "拖拉机",
    "trailer": "拖车",
    "train": "列车",
    "trajectory": "轨迹",
    "transducer": "传感器",
    "transfer": "转移",
    "transformer": "变压器",
    "transient": "瞬态",
    "transistor": "晶体管",
    "transition": "转变",
    "transmission": "传动",
    "transmitter": "变送器",
    "transparent": "透明",
    "transport": "运输",
    "transverse": "横向",
    "trap": "疏水阀",
    "travel": "行程",
    "tray": "托盘",
    "treatment": "处理",
    "trench": "沟",
    "triangulation": "三角测量",
    "tribology": "摩擦学",
    "trigger": "触发",
    "trim": "修整",
    "trimmer": "修边机",
    "triode": "三极管",
    "trip": "跳闸",
    "trochoid": "次摆线",
    "trolley": "小车",
    "trouble": "故障",
    "trough": "槽",
    "truck": "卡车",
    "true": "真",
    "trunnion": "耳轴",
    "truss": "桁架",
    "tube": "管",
    "tube sheet": "管板",
    "tubing": "管材",
    "tumble": "翻滚",
    "tungsten": "钨",
    "tuning": "调谐",
    "tunnel": "隧道",
    "turbine": "涡轮",
    "turbo": "涡轮",
    "turbocompressor": "涡轮压缩机",
    "turbofan": "涡轮风扇",
    "turbojet": "涡轮喷气",
    "turbomachinery": "涡轮机械",
    "turbopump": "涡轮泵",
    "turbulence": "湍流",
    "turn": "转",
    "turnbuckle": "花篮螺丝",
    "turning": "车削",
    "turntable": "转台",
    "tuyere": "风口",
    "twin": "双",
    "twist": "扭转",
    "two-phase": "两相",
    "type": "类型",
    # U
    "ultimate": "极限",
    "ultrasonic": "超声",
    "ultrasonic testing": "超声检测",
    "ultrasound": "超声",
    "ultraviolet": "紫外",
    "unbalance": "不平衡",
    "uncertainty": "不确定度",
    "underwater": "水下",
    "uniaxial": "单轴",
    "uniform": "均匀",
    "union": "活接头",
    "unit": "单元",
    "universal": "万向",
    "universal joint": "万向节",
    "unloader": "卸载机",
    "unsteady": "非稳态",
    "upgrade": "升级",
    "upper": "上",
    "upright": "立柱",
    "upset": "镦粗",
    "upstream": "上游",
    "urethane": "聚氨酯",
    "utility": "公用工程",
    # V
    "vacuum": "真空",
    "vacuum pump": "真空泵",
    "validation": "验证",
    "valve": "阀",
    "vane": "叶片",
    "vapor": "蒸汽",
    "vaporization": "汽化",
    "variable": "变量",
    "variance": "方差",
    "variation": "变化",
    "varnish": "清漆",
    "vector": "矢量",
    "vehicle": "车辆",
    "velocity": "速度",
    "vent": "通风口",
    "ventilation": "通风",
    "venturi": "文丘里管",
    "verification": "验证",
    "vernier": "游标",
    "vertical": "垂直",
    "vessel": "容器",
    "vibrating": "振动",
    "vibration": "振动",
    "vibrator": "振动器",
    "view": "视图",
    "viscoelastic": "粘弹性",
    "viscometer": "粘度计",
    "viscosity": "粘度",
    "viscous": "粘性",
    "voltage": "电压",
    "voltmeter": "电压表",
    "volume": "体积",
    "volumetric": "容积",
    "vortex": "涡流",
    # W
    "wall": "壁",
    "warehouse": "仓库",
    "warm": "温暖",
    "warmer": "加热器",
    "warming": "加热",
    "warranty": "保修",
    "wash": "清洗",
    "washer": "垫圈",
    "washing": "清洗",
    "waste": "废物",
    "watch": "手表",
    "water": "水",
    "water hammer": "水锤",
    "water jacket": "水套",
    "water pump": "水泵",
    "waterproof": "防水",
    "watt": "瓦特",
    "wave": "波",
    "wavelength": "波长",
    "wax": "蜡",
    "wear": "磨损",
    "weather": "天气",
    "weathering": "风化",
    "web": "腹板",
    "wedge": "楔",
    "weigh": "称重",
    "weighing": "称重",
    "weight": "重量",
    "weld": "焊接",
    "welding": "焊接",
    "welding rod": "焊条",
    "well": "井",
    "wet": "湿",
    "wetness": "湿度",
    "wheel": "轮",
    "width": "宽度",
    "winch": "绞车",
    "wind": "风",
    "wind energy": "风能",
    "wind tunnel": "风洞",
    "winding": "绕组",
    "window": "窗",
    "wiper": "刮水器",
    "wire": "线材",
    "wire rope": "钢丝绳",
    "wiring": "接线",
    "withdrawal": "撤回",
    "wood": "木材",
    "work": "功",
    "work hardening": "加工硬化",
    "workpiece": "工件",
    "workshop": "车间",
    "worm": "蜗杆",
    "worm drive": "蜗杆传动",
    "worm gear": "蜗轮",
    "wrench": "扳手",
    "wrinkle": "皱纹",
    # X
    "xenon": "氙",
    "x-ray": "X射线",
    # Y
    "yarn": "纱线",
    "yield": "屈服",
    "yield strength": "屈服强度",
    "yoke": "轭",
    # Z
    "zener": "齐纳",
    "zero": "零",
    "zinc": "锌",
    "zirconium": "锆",
    "zone": "区域",
}

# ================================================================
# Common technical suffixes and their Chinese translations
# ================================================================
SUFFIX_TRANSLATIONS = {
    "machine": "机",
    "machine tool": "机床",
    "device": "装置",
    "equipment": "设备",
    "system": "系统",
    "valve": "阀",
    "pump": "泵",
    "motor": "电机",
    "engine": "发动机",
    "compressor": "压缩机",
    "turbine": "涡轮机",
    "generator": "发电机",
    "sensor": "传感器",
    "actuator": "执行器",
    "controller": "控制器",
    "regulator": "调节器",
    "indicator": "指示器",
    "meter": "计",
    "gauge": "表",
    "gages": "量规",
    "tool": "工具",
    "cutter": "刀具",
    "drill": "钻头",
    "reamer": "铰刀",
    "broach": "拉刀",
    "tap": "丝锥",
    "die": "模具",
    "mold": "模具",
    "fixture": "夹具",
    "jig": "钻模",
    "chuck": "卡盘",
    "bearing": "轴承",
    "spring": "弹簧",
    "gear": "齿轮",
    "coupling": "联轴器",
    "clutch": "离合器",
    "brake": "制动器",
    "damper": "阻尼器",
    "shock absorber": "减震器",
    "silencer": "消声器",
    "filter": "过滤器",
    "strainer": "过滤器",
    "separator": "分离器",
    "dryer": "干燥器",
    "cooler": "冷却器",
    "heater": "加热器",
    "condenser": "冷凝器",
    "evaporator": "蒸发器",
    "exchanger": "交换器",
    "boiler": "锅炉",
    "furnace": "炉",
    "kiln": "窑",
    "reactor": "反应器",
    "column": "塔",
    "tower": "塔",
    "tank": "罐",
    "vessel": "容器",
    "chamber": "室",
    "cylinder": "缸",
    "piston": "活塞",
    "nozzle": "喷嘴",
    "orifice": "孔板",
    "manifold": "歧管",
    "header": "集管",
    "pipe": "管",
    "tube": "管",
    "hose": "软管",
    "duct": "管道",
    "conduit": "导管",
    "fitting": "管件",
    "flange": "法兰",
    "gasket": "垫片",
    "seal": "密封",
    "packing": "填料",
    "ring": "环",
    "washer": "垫圈",
    "nut": "螺母",
    "bolt": "螺栓",
    "screw": "螺钉",
    "rivet": "铆钉",
    "key": "键",
    "pin": "销",
    "shaft": "轴",
    "axle": "车轴",
    "spindle": "主轴",
    "rod": "杆",
    "bar": "棒",
    "plate": "板",
    "sheet": "薄板",
    "beam": "梁",
    "column": "柱",
    "frame": "框架",
    "housing": "壳体",
    "casing": "壳体",
    "cover": "盖",
    "cap": "盖",
    "plug": "塞",
    "base": "基座",
    "pedestal": "底座",
    "bracket": "支架",
    "support": "支撑",
    "mount": "安装座",
    "adapter": "适配器",
    "connector": "连接器",
    "joint": "接头",
    "coupler": "耦合器",
    "converter": "转换器",
    "transducer": "传感器",
    "transmitter": "变送器",
    "receiver": "接收器",
    "amplifier": "放大器",
    "rectifier": "整流器",
    "inverter": "逆变器",
    "transformer": "变压器",
    "switch": "开关",
    "breaker": "断路器",
    "relay": "继电器",
    "contactor": "接触器",
    "solenoid": "电磁阀",
    "valve": "阀",
    "calculator": "计算器",
    "formula": "公式",
    "equation": "方程",
    "chart": "图",
    "diagram": "图",
    "table": "表",
    "graph": "图",
    "curve": "曲线",
    "design": "设计",
    "analysis": "分析",
    "calculation": "计算",
    "testing": "试验",
    "inspection": "检验",
    "calibration": "校准",
    "maintenance": "维护",
    "repair": "维修",
    "installation": "安装",
    "operation": "操作",
    "process": "工艺",
    "method": "方法",
    "technique": "技术",
    "technology": "技术",
    "material": "材料",
    "alloy": "合金",
    "steel": "钢",
    "metal": "金属",
    "plastic": "塑料",
    "ceramic": "陶瓷",
    "composite": "复合材料",
    "polymer": "聚合物",
    "rubber": "橡胶",
    "wood": "木材",
    "glass": "玻璃",
    "casting": "铸造",
    "forging": "锻造",
    "machining": "机加工",
    "welding": "焊接",
    "forming": "成形",
    "stamping": "冲压",
    "molding": "模塑",
    "extrusion": "挤压",
    "annealing": "退火",
    "quenching": "淬火",
    "hardening": "硬化",
    "tempering": "回火",
    "polishing": "抛光",
    "grinding": "磨削",
    "milling": "铣削",
    "drilling": "钻孔",
    "turning": "车削",
    "boring": "镗孔",
    "broaching": "拉削",
    "hobbing": "滚齿",
    "shaping": "刨削",
    "sawing": "锯削",
    "lapping": "研磨",
}

TWO_WORD_SUFFIX_MAP = {
    "heat exchanger": "换热器",
    "heat engine": "热机",
    "heat pump": "热泵",
    "steam turbine": "汽轮机",
    "gas turbine": "燃气轮机",
    "wind turbine": "风力发电机",
    "hydraulic cylinder": "液压缸",
    "hydraulic motor": "液压马达",
    "hydraulic pump": "液压泵",
    "pneumatic cylinder": "气缸",
    "solenoid valve": "电磁阀",
    "control valve": "控制阀",
    "check valve": "止回阀",
    "ball valve": "球阀",
    "butterfly valve": "蝶阀",
    "globe valve": "截止阀",
    "gate valve": "闸阀",
    "needle valve": "针形阀",
    "relief valve": "泄压阀",
    "safety valve": "安全阀",
    "pressure vessel": "压力容器",
    "ball bearing": "球轴承",
    "roller bearing": "滚子轴承",
    "thrust bearing": "推力轴承",
    "plain bearing": "滑动轴承",
    "bevel gear": "锥齿轮",
    "spur gear": "直齿轮",
    "helical gear": "斜齿轮",
    "worm gear": "蜗轮",
    "planetary gear": "行星齿轮",
    "belt drive": "皮带传动",
    "chain drive": "链传动",
    "gear drive": "齿轮传动",
    "lead screw": "丝杠",
    "ball screw": "滚珠丝杠",
    "universal joint": "万向节",
    "connecting rod": "连杆",
    "crankshaft": "曲轴",
    "camshaft": "凸轮轴",
    "drive shaft": "驱动轴",
    "gear box": "齿轮箱",
    "internal combustion": "内燃机",
    "fuel injection": "燃油喷射",
    "spark plug": "火花塞",
    "air compressor": "空压机",
    "centrifugal pump": "离心泵",
    "gear pump": "齿轮泵",
    "screw pump": "螺杆泵",
    "piston pump": "活塞泵",
    "vacuum pump": "真空泵",
    "axial flow": "轴流",
    "water pump": "水泵",
    "oil pump": "油泵",
    "heat treatment": "热处理",
    "surface hardening": "表面硬化",
    "case hardening": "渗碳硬化",
    "flame hardening": "火焰淬火",
    "induction hardening": "感应淬火",
    "shot peening": "喷丸",
    "sand blasting": "喷砂",
    "metal cutting": "金属切削",
    "laser cutting": "激光切割",
    "plasma cutting": "等离子切割",
    "water jet": "水射流",
    "wire edm": "线切割",
    "electric motor": "电动机",
    "servo motor": "伺服电机",
    "step motor": "步进电机",
    "induction motor": "感应电机",
    "steam generator": "蒸汽发生器",
    "air conditioner": "空调",
    "air handler": "空气处理机",
    "cooling tower": "冷却塔",
    "heat recovery": "热回收",
    "pressure gauge": "压力表",
    "flow meter": "流量计",
    "temperature sensor": "温度传感器",
    "strain gauge": "应变片",
    "torque converter": "变矩器",
    "fluid coupling": "液力耦合器",
    "power transmission": "动力传输",
    "tensile strength": "抗拉强度",
    "yield strength": "屈服强度",
    "fatigue strength": "疲劳强度",
    "compressive strength": "抗压强度",
    "shear stress": "剪切应力",
    "shear modulus": "剪切模量",
    "bulk modulus": "体积模量",
    "young modulus": "杨氏模量",
    "thermal conductivity": "热导率",
    "thermal expansion": "热膨胀",
    "natural frequency": "固有频率",
    "boundary layer": "边界层",
    "finite element": "有限元",
    "stress concentration": "应力集中",
    "corrosion resistance": "耐腐蚀性",
    "wear resistance": "耐磨性",
    "fatigue life": "疲劳寿命",
    "quality control": "质量控制",
    "non destructive": "无损检测",
    "computer aided": "计算机辅助",
    "computer numerical": "计算机数控",
    "programmable logic": "可编程逻辑",
}

PREFIX_MAP = {
    "micro": "微",
    "macro": "宏观",
    "mini": "微型",
    "nano": "纳米",
    "auto": "自动",
    "semi": "半",
    "multi": "多",
    "poly": "多",
    "bi": "双",
    "tri": "三",
    "quad": "四",
    "thermo": "热",
    "hydro": "水",
    "electro": "电",
    "pneumato": "气动",
    "aero": "空气",
    "tribo": "摩擦",
    "mechano": "机械",
    "opto": "光学",
    "piezo": "压电",
    "ferro": "铁",
    "cryo": "低温",
    "iso": "等",
}

# Variant generation rules
VARIANT_RULES = [
    # (pattern_name, base_suffix, replacements_to_add)
    # steel type variants
    ("steel_alloys", "steel", [
        "carbon steel", "alloy steel", "stainless steel", "tool steel",
        "die steel", "high speed steel", "spring steel", "bearing steel",
        "structural steel", "mild steel", "cold rolled steel",
        "hot rolled steel", "galvanized steel", "silicon steel",
        "manganese steel", "chromium steel", "nickel steel",
        "vanadium steel", "tungsten steel", "molybdenum steel",
    ]),
    # iron variants
    ("iron_types", "iron", [
        "cast iron", "ductile iron", "malleable iron", "wrought iron",
        "gray iron", "white iron", "nodular iron", "alloy iron",
    ]),
    # machine tool variants
    ("machine_tools", "machine", [
        "milling machine", "grinding machine", "boring machine",
        "drilling machine", "planing machine", "shaping machine",
        "slotting machine", "broaching machine", "sawing machine",
        "hobbing machine", "gear cutting machine", "thread milling machine",
        "jig boring machine", "cylindrical grinding machine",
        "surface grinding machine", "centerless grinding machine",
    ]),
    # pump variants
    ("pump_types", "pump", [
        "centrifugal pump", "reciprocating pump", "diaphragm pump",
        "gear pump", "screw pump", "vane pump", "piston pump",
        "plunger pump", "peristaltic pump", "lobe pump",
        "vacuum pump", "submersible pump", "booster pump",
        "metering pump", "hydraulic pump", "canned pump",
        "slurry pump", "circulating pump", "jet pump",
        "axial flow pump", "mixed flow pump",
    ]),
    # valve variants
    ("valve_types", "valve", [
        "gate valve", "globe valve", "ball valve", "butterfly valve",
        "check valve", "relief valve", "safety valve", "control valve",
        "solenoid valve", "needle valve", "plug valve",
        "diaphragm valve", "pinch valve", "knife gate valve",
        "pressure reducing valve", "pressure relief valve",
        "sequence valve", "proportional valve", "servo valve",
    ]),
    # bearing variants
    ("bearing_types", "bearing", [
        "ball bearing", "roller bearing", "thrust bearing",
        "needle bearing", "tapered roller bearing", "spherical roller bearing",
        "cylindrical roller bearing", "angular contact bearing",
        "deep groove ball bearing", "self aligning bearing",
        "plain bearing", "journal bearing", "sleeve bearing",
        "fluid bearing", "magnetic bearing", "air bearing",
    ]),
    # gear variants
    ("gear_types", "gear", [
        "spur gear", "helical gear", "bevel gear", "worm gear",
        "rack and pinion", "planetary gear", "hypoid gear",
        "miter gear", "internal gear", "herringbone gear",
        "spiral bevel gear", "straight bevel gear",
    ]),
    # spring variants
    ("spring_types", "spring", [
        "compression spring", "tension spring", "torsion spring",
        "helical spring", "leaf spring", "coil spring",
        "belleville spring", "wave spring", "gas spring",
        "die spring", "extension spring", "constant force spring",
    ]),
    # fastener variants
    ("fastener_types", "bolt", [
        "hex bolt", "carriage bolt", "eye bolt", "anchor bolt",
        "u-bolt", "t-bolt", "shoulder bolt", "stud bolt",
        "machine screw", "set screw", "cap screw",
        "socket screw", "self tapping screw", "wood screw",
    ]),
    # welding variants
    ("welding_types", "welding", [
        "arc welding", "spot welding", "seam welding",
        "tig welding", "mig welding", "submerged arc welding",
        "laser welding", "ultrasonic welding", "friction welding",
        "resistance welding", "electron beam welding",
        "gas welding", "forge welding", "stud welding",
    ]),
    # casting variants
    ("casting_types", "casting", [
        "sand casting", "die casting", "investment casting",
        "centrifugal casting", "continuous casting", "shell casting",
        "gravity casting", "low pressure casting", "squeeze casting",
        "lost foam casting", "vacuum casting",
    ]),
    # heat treatment variants
    ("heat_treatment", "treatment", [
        "heat treatment", "surface treatment", "cryogenic treatment",
        "stress relief", "solution treatment", "aging treatment",
    ]),
    # forging variants
    ("forging_types", "forging", [
        "open die forging", "closed die forging", "hot forging",
        "cold forging", "warm forging", "drop forging",
        "upset forging", "roll forging", "press forging",
        "precision forging", "isothermal forging",
    ]),
    # motor variants
    ("motor_types", "motor", [
        "electric motor", "hydraulic motor", "pneumatic motor",
        "servo motor", "stepper motor", "induction motor",
        "synchronous motor", "dc motor", "ac motor",
        "linear motor", "gear motor", "torque motor",
    ]),
    # sensor variants
    ("sensor_types", "sensor", [
        "temperature sensor", "pressure sensor", "flow sensor",
        "position sensor", "proximity sensor", "level sensor",
        "force sensor", "torque sensor", "speed sensor",
        "vibration sensor", "displacement sensor", "accelerometer",
        "strain sensor", "humidity sensor", "photoelectric sensor",
        "ultrasonic sensor", "laser sensor", "vision sensor",
    ]),
    # alloy variants
    ("aluminum_alloys", "aluminum", [
        "aluminum alloy", "aluminum casting", "aluminum extrusion",
        "wrought aluminum", "cast aluminum", "aluminum bronze",
    ]),
    # copper alloy variants
    ("copper_alloys", "copper", [
        "copper alloy", "copper tube", "copper pipe",
        "beryllium copper", "phosphor bronze", "aluminum bronze",
        "brass", "naval brass", "red brass",
    ]),
    # cooling variants
    ("cooling_types", "cooling", [
        "air cooling", "water cooling", "oil cooling",
        "forced cooling", "natural cooling", "evaporative cooling",
        "cooling system", "cooling tower", "cooling fin",
    ]),
    # Lubrication variants
    ("lubrication_types", "lubrication", [
        "oil lubrication", "grease lubrication", "mist lubrication",
        "forced lubrication", "splash lubrication", "centralized lubrication",
        "lubrication system", "lubrication oil", "lubrication pump",
    ]),
    # Pipe fitting variants
    ("pipe_fittings", "pipe", [
        "steel pipe", "seamless pipe", "welded pipe",
        "pipe fitting", "pipe flange", "pipe joint",
        "pipe support", "pipe hanger", "pipe insulation",
        "pipe bend", "pipe elbow", "pipe tee",
    ]),
    # Cylinder variants
    ("cylinder_types", "cylinder", [
        "hydraulic cylinder", "pneumatic cylinder", "single acting cylinder",
        "double acting cylinder", "telescopic cylinder", "rotary cylinder",
        "tie rod cylinder", "welded cylinder", "cylinder barrel",
        "cylinder head", "cylinder liner", "cylinder block",
    ]),
]

# ================================================================
# Term extraction helpers
# ================================================================
def normalize_term(s):
    """Normalize an English term for dedup lookup"""
    s = s.strip().lower()
    s = re.sub(r'\s+', ' ', s)
    return s

def is_technical_title(title):
    """Filter out non-technical pages"""
    skip_words = [
        "list of", "index of", "category:", "template:", "wikipedia:",
        "file:", "help:", "portal:", "talk:", "discussion", "forum",
    ]
    t = title.lower()
    for sw in skip_words:
        if t.startswith(sw):
            return False
    # Skip very long titles
    if len(title) > 80:
        return False
    return True

def extract_core_term_from_title(title):
    """Extract core engineering term from a descriptive title.
    Handles Wikipedia page titles and engineers-edge page titles.
    """
    t = title.strip()

    # Remove parenthetical qualifiers
    t = re.sub(r'\s*\(.*?\)\s*', ' ', t).strip()

    # For Wikipedia, the title itself is often a good term
    return t

def classify_wikipedia_page(categories):
    """Map Wikipedia categories to our classification system."""
    if not categories:
        return "未分类"

    for cat in categories:
        cat_lower = cat.lower()
        if "mechanical engineering" in cat_lower or "machine element" in cat_lower:
            return "机械设计"
        if "manufacturing" in cat_lower or "machining" in cat_lower or "casting" in cat_lower or "welding" in cat_lower:
            return "制造工艺"
        if "heat transfer" in cat_lower or "fluid" in cat_lower or "thermo" in cat_lower or "hydraulic" in cat_lower:
            return "热工流体"
        if "material" in cat_lower or "metal" in cat_lower or "alloy" in cat_lower or "steel" in cat_lower or "polymer" in cat_lower:
            return "工程材料"
        if "engine" in cat_lower or "motor" in cat_lower or "automation" in cat_lower or "robot" in cat_lower or "electri" in cat_lower:
            return "机电自动化"
        if "stress" in cat_lower or "strength" in cat_lower or "vibration" in cat_lower or "mechanics" in cat_lower:
            return "力学强度"
        if "design" in cat_lower or "cad" in cat_lower or "drafting" in cat_lower or "drawing" in cat_lower:
            return "制图CAD"
        if "standard" in cat_lower or "code" in cat_lower or "regulation" in cat_lower:
            return "标准规范"
    return "机械设计"  # default for mechanical engineering pages


def classify_by_title_and_content(title, content=""):
    """Classify a term based on title and content keywords."""
    combined = (title + " " + content).lower()

    # Manufacturing keywords
    mfg_kw = ["casting", "forging", "machining", "welding", "stamping", "molding",
              "extrusion", "annealing", "quenching", "tempering", "heat treatment",
              "forming", "rolling", "drawing", "cutting", "grinding", "milling",
              "drilling", "turning", "boring", "broaching", "hobbing", "lathing",
              "polishing", "plating", "coating", "painting", "manufacturing",
              "fabrication", "assembly", "production", "process"]
    mfg_score = sum(1 for kw in mfg_kw if kw in combined)

    # Materials keywords
    mat_kw = ["steel", "alloy", "aluminum", "copper", "iron", "titanium", "nickel",
              "metal", "plastic", "polymer", "ceramic", "composite", "material",
              "stainless", "bronze", "brass", "zinc", "magnesium", "carbon",
              "hardness", "tensile", "yield", "fatigue", "corrosion"]
    mat_score = sum(1 for kw in mat_kw if kw in combined)

    # Thermal/fluid keywords
    th_kw = ["heat", "temperature", "fluid", "flow", "pressure", "thermal",
             "thermo", "hydraulic", "pneumatic", "steam", "gas", "liquid",
             "pump", "valve", "pipe", "boiler", "condenser", "exchanger",
             "cooling", "heating", "ventilation", "air", "compressor",
             "turbine", "engine", "combustion"]
    th_score = sum(1 for kw in th_kw if kw in combined)

    # Machine design keywords
    md_kw = ["gear", "bearing", "spring", "shaft", "screw", "bolt", "nut",
             "fastener", "coupling", "clutch", "brake", "belt", "chain",
             "cam", "linkage", "bearing", "seal", "gasket", "flange",
             "design", "stress", "strain", "load", "torque", "beam",
             "deflection", "fatigue", "vibration", "mechanism"]
    md_score = sum(1 for kw in md_kw if kw in combined)

    # Automation keywords
    auto_kw = ["motor", "actuator", "sensor", "controller", "robot", "servo",
               "automation", "control", "plc", "programmable", "encoder",
               "solenoid", "electrical", "electronic", "digital", "feedback",
               "hydraulic", "pneumatic", "cylinder", "valve", "position"]
    auto_score = sum(1 for kw in auto_kw if kw in combined)

    # CAD keywords
    cad_kw = ["cad", "drawing", "drafting", "dimension", "tolerance", "gdt",
              "solid model", "surface model", "parametric", "assembly",
              "blueprint", "schematic", "diagram", "3d model", "sketch"]
    cad_score = sum(1 for kw in cad_kw if kw in combined)

    scores = [
        ("制造工艺", mfg_score),
        ("工程材料", mat_score),
        ("热工流体", th_score),
        ("机械设计", md_score),
        ("机电自动化", auto_score),
        ("制图CAD", cad_score),
    ]

    # Choose the category with highest score, break ties by priority
    best = max(scores, key=lambda x: x[1])
    if best[1] > 0:
        return best[0]
    return "未分类"


def en_to_zh(en_term):
    """Translate an English engineering term to Chinese using dictionary.
    Returns (zh_term, confidence: high/medium/low)
    """
    term_lower = en_term.strip().lower()

    # 1. Exact match in dictionary
    if term_lower in EN2ZH_DICT:
        return EN2ZH_DICT[term_lower], "high"

    # 2. Check two-word suffix map
    if term_lower in TWO_WORD_SUFFIX_MAP:
        return TWO_WORD_SUFFIX_MAP[term_lower], "high"

    # 3. Strip suffix words and look up the prefix
    # Common trailing filler words to strip
    strip_words = ["calculator", "calculators", "formula", "formulas",
                   "design", "equations", "equation", "chart", "table",
                   "diagram", "graph", "selection", "guide", "handbook",
                   "manual", "data", "information", "reference", "menu",
                   "application", "engineering", "basics", "fundamentals",
                   "principles", "overview", "introduction", "general",
                   "common", "standard", "typical", "analysis", "calculation",
                   "theory", "concepts", "and", "the", "of"]

    words = term_lower.split()
    # Try progressively shorter prefixes
    for end in range(len(words), 0, -1):
        prefix = " ".join(words[:end])
        if end < len(words):
            remaining = words[end:]
            if all(w in strip_words for w in remaining):
                if prefix in EN2ZH_DICT:
                    return EN2ZH_DICT[prefix], "medium"
                if prefix in TWO_WORD_SUFFIX_MAP:
                    return TWO_WORD_SUFFIX_MAP[prefix], "medium"

    # 4. Try stripping trailing words one by one
    for i in range(len(words)-1, 0, -1):
        prefix = " ".join(words[:i])
        if prefix in EN2ZH_DICT:
            return EN2ZH_DICT[prefix], "medium"
        if prefix in TWO_WORD_SUFFIX_MAP:
            return TWO_WORD_SUFFIX_MAP[prefix], "medium"
        # Check if remaining is a known suffix
        suffix = " ".join(words[i:])
        if suffix in SUFFIX_TRANSLATIONS:
            zh_prefix, _ = en_to_zh(prefix)
            if zh_prefix != prefix:  # we got a translation
                return zh_prefix + SUFFIX_TRANSLATIONS[suffix], "medium"

    # 5. Word-by-word translation for compound terms
    zh_words = []
    untranslated = []
    for w in words:
        if w in EN2ZH_DICT:
            zh_words.append(EN2ZH_DICT[w])
        elif w in SUFFIX_TRANSLATIONS:
            zh_words.append(SUFFIX_TRANSLATIONS[w])
        else:
            untranslated.append(w)
            zh_words.append(w)

    if zh_words and all(z == w for z, w in zip(zh_words, words)):
        # No translation found at all
        pass
    elif zh_words:
        return "".join(zh_words), "low"

    # 6. Check if the term is a noun phrase ending with -er/-or/-ing
    last_word = words[-1] if words else ""
    if last_word.endswith("er") or last_word.endswith("or"):
        base = last_word[:-2] if last_word.endswith("er") else last_word[:-2]
        if base in EN2ZH_DICT:
            zh_base = EN2ZH_DICT[base]
            prefix = " ".join(words[:-1])
            if prefix:
                zh_prefix, _ = en_to_zh(prefix)
                if zh_prefix != prefix:
                    return zh_prefix + zh_base + "器", "low"
            return zh_base + "器", "low"

    if last_word.endswith("ing"):
        base = last_word[:-3]
        if base in EN2ZH_DICT:
            zh_base = EN2ZH_DICT[base]
            return zh_base + "加工", "low"

    # 7. Fallback: use English term directly
    return en_term, "low"


def generate_definition(en_term, extract=None, content=None):
    """Generate a definition for a term."""
    if extract and len(extract) > 20:
        # Use Wikipedia extract, first 200 chars
        return extract[:200].strip()

    if content and len(content) > 30:
        # Use content text, first 200 chars
        # Try to find a meaningful sentence
        sentences = re.split(r'(?<=[.!])\s+', content)
        for s in sentences:
            s = s.strip()
            if len(s) > 30 and len(s) < 250:
                return s[:200].strip()
        return content[:200].strip()

    # Generate from English term
    zh, _ = en_to_zh(en_term)
    return f"{en_term} 是机械工程中{zh}相关的术语。"


def extract_engineers_edge_terms(records):
    """Extract engineering terms from Engineers Edge records."""
    terms = []
    seen_titles = set()

    # Common non-term patterns to skip
    skip_patterns = [
        r'^\s*$', r'advertisement', r'privacy', r'login', r'register',
        r'sign.?in', r'copyright', r'disclaimer', r'search',
        r'shopping cart', r'checkout', r'my account',
        r'cookie', r'site map', r'contact us', r'about us',
    ]

    for record in records:
        title = record.get("title", "").strip()
        text = record.get("text", "")

        if not title:
            continue

        title_lower = title.lower()
        if any(re.search(p, title_lower) for p in skip_patterns):
            continue

        # Skip if title is too short or too long
        if len(title) < 5 or len(title) > 120:
            continue

        # Normalize for dedup
        key = normalize_term(title)
        if key in seen_titles:
            continue
        seen_titles.add(key)

        # Extract core entity from title
        # Remove trailing filler words
        entity = extract_core_entity(title)
        if not entity or len(entity) < 3:
            continue

        entity_key = normalize_term(entity)
        if entity_key in seen_titles:
            continue

        zh_term, confidence = en_to_zh(entity)
        category = classify_by_title_and_content(entity, text)
        definition = generate_definition(entity, content=text)

        terms.append({
            "en": entity,
            "zh": zh_term,
            "definition": definition,
            "source": "engineers-edge",
            "category": category,
            "translation_confidence": confidence,
        })

    return terms


def extract_core_entity(title):
    """Extract core engineering entity from a descriptive page title.
    E.g., 'Beam Deflection Calculator and Beam Stress Formulas' -> 'Beam Deflection'
    """
    # Remove parenthetical qualifiers
    t = re.sub(r'\s*\(.*?\)\s*', ' ', title).strip()

    # Remove ISO/standard references
    t = re.sub(r'\b(per\.?|ISO|ASTM|ANSI|DIN|JIS|ASME|SAE|IEEE)\s*[\d\s\-]+\b', '', t, flags=re.IGNORECASE)

    # Remove trailing filler words (reduce to core entity)
    filler_patterns = [
        r'\s+(calculator|calculators|formulas?|equations?|chart|table|diagram|graph)\s*$',
        r'\s+(design|analysis|calculation|application)\s*$',
        r'\s+(selection|guide|handbook|manual|reference|data|information)\s*$',
        r'\s+(menu|overview|introduction|basics|fundamentals|principles)\s*$',
        r'\s+(and|or|the)\s+.*$',  # truncate at conjunctions
        r'\s+(per\.?)\s+.*$',
    ]

    for pat in filler_patterns:
        t = re.sub(pat, '', t, flags=re.IGNORECASE).strip()

    # Remove leading "Conversion of", "Design of", "Calculation of", etc.
    lead_patterns = [
        r'^conversion\s+of\s+',
        r'^design\s+of\s+',
        r'^calculation\s+of\s+',
        r'^analysis\s+of\s+',
        r'^introduction\s+to\s+',
        r'^overview\s+of\s+',
        r'^basics\s+of\s+',
        r'^fundamentals?\s+of\s+',
        r'^principles?\s+of\s+',
    ]
    for pat in lead_patterns:
        t = re.sub(pat, '', t, flags=re.IGNORECASE).strip()

    # Clean up
    t = re.sub(r'\s+', ' ', t).strip()
    t = t.strip(' ,;:.!?-')

    return t


def extract_wikipedia_terms(pages_data):
    """Extract terms from Wikipedia pages."""
    terms = []
    seen = set()

    categories = pages_data.get("categories", {})
    for wiki_cat, pages in categories.items():
        our_cat = CATEGORY_MAP_WIKI.get(wiki_cat, "机械设计")

        for page in pages:
            title = page.get("title", "").strip()
            extract_text = page.get("extract", "")

            if not title or not is_technical_title(title):
                continue

            # Extract core entity - Wikipedia titles are usually good terms
            entity = extract_core_term_from_title(title)
            entity_key = normalize_term(entity)
            if entity_key in seen:
                continue
            seen.add(entity_key)

            zh_term, confidence = en_to_zh(entity)
            definition = generate_definition(entity, extract=extract_text)

            terms.append({
                "en": entity,
                "zh": zh_term,
                "definition": definition,
                "source": "wikipedia",
                "category": our_cat,
                "translation_confidence": confidence,
            })

    return terms


def extract_efunda_terms(records):
    """Extract terms from eFunda records."""
    terms = []
    seen = set()

    non_content_sections = {"materials"}  # Too generic

    # Entities to extract from efunda content
    # The content text has sections like: Materials, Design Center, Processes, etc.
    entity_patterns = [
        (r'(3D\s+Printing)', "制造工艺", "3D打印"),
        (r'(CNC\s+Machining)', "制造工艺", "数控加工"),
        (r'(Injection\s+Molding)', "制造工艺", "注塑成型"),
        (r'(Rapid\s+Prototyping)', "制造工艺", "快速原型"),
        (r'((?:Gear|Spring|Bearing|Screw|Beam|O-Ring|Piping|Valve|Flange|Pump|Compressor|Turbine)\s*(?:Design|Calculator|Formulas?|Engineering|Selection)?\b)',
         "机械设计", None),
    ]

    for record in records:
        title = record.get("title", "")
        content = record.get("content", "")

        # Extract entities from content text
        # Look for section headings and key terms
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue

            # Look for engineering terms in the content
            # These are usually capitalized terms
            for match in re.finditer(r'(?<![a-z])([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', line):
                entity = match.group(1).strip()
                if len(entity) < 4 or len(entity) > 50:
                    continue

                # Filter out URLs and non-technical terms
                if entity.startswith("Http") or entity.startswith("www"):
                    continue

                key = normalize_term(entity)
                if key in seen:
                    continue

                # Check if it looks like an engineering term
                tech_indicators = [
                    "Design", "Engineering", "Calculator", "Formula", "Material",
                    "Process", "Machine", "System", "Device", "Method",
                    "Steel", "Alloy", "Metal", "Plastic", "Composite",
                    "Valve", "Pump", "Gear", "Bearing", "Spring", "Shaft",
                    "Testing", "Analysis", "Inspection", "Standard",
                    "Stress", "Strain", "Force", "Pressure", "Temperature",
                ]
                if not any(ind in entity for ind in tech_indicators):
                    continue

                seen.add(key)
                zh_term, confidence = en_to_zh(entity)
                category = classify_by_title_and_content(entity, content)
                definition = generate_definition(entity, content=content)

                terms.append({
                    "en": entity,
                    "zh": zh_term,
                    "definition": definition,
                    "source": "efunda",
                    "category": category,
                    "translation_confidence": confidence,
                })

    return terms


def extract_toolbox_terms(records):
    """Extract terms from Engineering Toolbox records."""
    terms = []
    seen = set()

    for record in records:
        title = record.get("title", "").strip()
        content = record.get("content", "")

        if not title:
            continue

        # Extract core entity from title
        title_clean = re.sub(r'\s*[-–—]\s*.*$', '', title)  # Remove subtitle after dash
        title_clean = re.sub(r'\s*\(.*?\)\s*', ' ', title_clean).strip()

        # Split on common delimiters to find engineering topics
        # e.g., "Water Density, Specific Weight and Thermal Expansion Coefficients"
        parts = re.split(r'\s*[,;]\s*|\s+and\s+', title_clean)
        for part in parts:
            part = part.strip()
            if not part or len(part) < 5:
                continue

            # Check if it's a meaningful engineering term
            if re.search(r'\b(?:Density|Weight|Pressure|Temperature|Flow|Heat|Stress|Strain|Force|Energy'
                         r'|Power|Efficiency|Viscosity|Conductivity|Expansion|Coefficient|Modulus|Ratio'
                         r'|Pipe|Valve|Pump|Tank|Boiler|Exchanger|Cooling|Heating|Ventilation|Air'
                         r'|Water|Steam|Gas|Liquid|Solid|Material|Steel|Metal|Alloy'
                         r'|Design|Calculation|Analysis|Testing|Standard)\b', part, re.IGNORECASE):

                key = normalize_term(part)
                if key in seen:
                    continue
                seen.add(key)

                zh_term, confidence = en_to_zh(part)
                category = classify_by_title_and_content(part, content)
                definition = generate_definition(part, content=content)

                terms.append({
                    "en": part,
                    "zh": zh_term,
                    "definition": definition,
                    "source": "engineering-toolbox",
                    "category": category,
                    "translation_confidence": confidence,
                })

    return terms


def generate_variant_terms(existing_terms):
    """Generate variant terms based on known rules."""
    variants = []
    seen_ens = set()

    # Build a set of existing English terms for dedup
    for t in existing_terms:
        seen_ens.add(normalize_term(t["en"]))

    # Process each variant rule
    for rule_name, base_term, replacements in VARIANT_RULES:
        for replacement in replacements:
            # The replacement should be a multi-word term
            # Use the last word as the category hint
            words = replacement.split()

            # Generate Chinese translation
            zh_term, confidence = en_to_zh(replacement)

            # Check dedup
            key = normalize_term(replacement)
            if key in seen_ens:
                continue
            seen_ens.add(key)

            # Determine category from the replacement
            category = classify_by_title_and_content(replacement)

            # Generate a definition
            definition = generate_definition(replacement)

            variants.append({
                "en": replacement,
                "zh": zh_term,
                "definition": definition,
                "source": "variant",
                "category": category,
                "translation_confidence": confidence,
            })

    return variants


def dedup_terms(existing_terms, new_terms):
    """Deduplicate new terms against existing ones by English name."""
    seen = set()
    for t in existing_terms:
        seen.add(normalize_term(t["en"]))

    deduped = []
    duplicates = 0
    for t in new_terms:
        key = normalize_term(t["en"])
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        deduped.append(t)

    return deduped, duplicates


def main():
    print("=" * 60)
    print("机械师大百科 — 术语扩展 V2")
    print("=" * 60)

    # 1. Load existing terms
    print("\n[1/6] Loading existing terms...")
    with open(TERM_FILE, 'r', encoding='utf-8') as f:
        term_data = json.load(f)

    existing_terms = term_data["terms"]
    existing_count = len(existing_terms)
    print(f"  Existing terms: {existing_count}")

    all_new_terms = []
    total_duplicates = 0

    # 2. Extract from Wikipedia
    print("\n[2/6] Extracting from Wikipedia (400 pages)...")
    try:
        with open(WIKI_FILE, 'r', encoding='utf-8') as f:
            wiki_data = json.load(f)
        wiki_terms = extract_wikipedia_terms(wiki_data)
        wiki_deduped, wiki_dups = dedup_terms(existing_terms, wiki_terms)
        all_new_terms.extend(wiki_deduped)
        total_duplicates += wiki_dups
        print(f"  Extracted: {len(wiki_terms)}, After dedup: {len(wiki_deduped)}, Duplicates: {wiki_dups}")
    except Exception as e:
        print(f"  ERROR: {e}")
        wiki_deduped = []

    # 3. Extract from Engineers Edge
    print("\n[3/6] Extracting from Engineers Edge...")
    combined_terms = existing_terms + all_new_terms
    ee_dir = os.path.join(PROJECT_ROOT, "raw", "engineers-edge")
    ee_terms = []
    for fn in sorted(os.listdir(ee_dir)):
        if fn.endswith('.json'):
            fp = os.path.join(ee_dir, fn)
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    extracted = extract_engineers_edge_terms(data)
                    ee_terms.extend(extracted)
                    print(f"  {fn}: {len(data)} records -> {len(extracted)} terms")
            except Exception as e:
                print(f"  {fn}: ERROR - {e}")

    ee_deduped, ee_dups = dedup_terms(combined_terms, ee_terms)
    all_new_terms.extend(ee_deduped)
    total_duplicates += ee_dups
    print(f"  Engineers Edge total extracted: {len(ee_terms)}, After dedup: {len(ee_deduped)}")

    # 4. Extract from eFunda
    print("\n[4/6] Extracting from eFunda...")
    combined_terms = existing_terms + all_new_terms
    efunda_dir = os.path.join(PROJECT_ROOT, "raw", "efunda")
    efunda_terms = []
    for fn in sorted(os.listdir(efunda_dir)):
        if fn.endswith('.json'):
            fp = os.path.join(efunda_dir, fn)
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    extracted = extract_efunda_terms(data)
                    efunda_terms.extend(extracted)
                    print(f"  {fn}: {len(data)} records -> {len(extracted)} terms")
            except Exception as e:
                print(f"  {fn}: ERROR - {e}")

    efunda_deduped, efunda_dups = dedup_terms(combined_terms, efunda_terms)
    all_new_terms.extend(efunda_deduped)
    total_duplicates += efunda_dups
    print(f"  eFunda total extracted: {len(efunda_terms)}, After dedup: {len(efunda_deduped)}")

    # 5. Extract from Engineering Toolbox
    print("\n[5/6] Extracting from Engineering Toolbox...")
    combined_terms = existing_terms + all_new_terms
    tb_dir = os.path.join(PROJECT_ROOT, "raw", "engineering-toolbox")
    tb_terms = []
    for fn in sorted(os.listdir(tb_dir)):
        if fn.endswith('.json'):
            fp = os.path.join(tb_dir, fn)
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    extracted = extract_toolbox_terms(data)
                    tb_terms.extend(extracted)
                    print(f"  {fn}: {len(data)} records -> {len(extracted)} terms")
            except Exception as e:
                print(f"  {fn}: ERROR - {e}")

    tb_deduped, tb_dups = dedup_terms(combined_terms, tb_terms)
    all_new_terms.extend(tb_deduped)
    total_duplicates += tb_dups
    print(f"  Toolbox total extracted: {len(tb_terms)}, After dedup: {len(tb_deduped)}")

    # 6. Generate variant terms
    print("\n[6/6] Generating variant terms...")
    combined_terms = existing_terms + all_new_terms
    variant_terms = generate_variant_terms(combined_terms)
    variant_deduped, variant_dups = dedup_terms(combined_terms, variant_terms)
    all_new_terms.extend(variant_deduped)
    total_duplicates += variant_dups
    print(f"  Generated: {len(variant_terms)}, After dedup: {len(variant_deduped)}")

    # ================================================================
    # Final assembly and output
    # ================================================================
    all_terms = existing_terms + all_new_terms

    # Remove the translation_confidence field from output
    for t in all_terms:
        t.pop("translation_confidence", None)

    # Count categories
    cat_counter = Counter()
    zh_none_count = 0
    def_none_count = 0
    for t in all_terms:
        cat_counter[t.get("category", "未分类")] += 1
        if not t.get("zh"):
            zh_none_count += 1
        if not t.get("definition"):
            def_none_count += 1

    # Count sources
    source_counter = Counter()
    for t in all_terms:
        source_counter[t.get("source", "unknown")] += 1

    # Update meta
    term_data["meta"]["total_terms"] = len(all_terms)
    term_data["meta"]["seed_terms"] = existing_count
    term_data["meta"]["expanded_new_terms"] = len(all_new_terms)
    term_data["meta"]["version"] = "2.1"
    term_data["meta"]["last_expanded"] = "2026-05-18"
    term_data["meta"]["data_sources"] = list(set(
        term_data["meta"].get("data_sources", []) +
        ["wikipedia", "engineers-edge", "efunda", "engineering-toolbox", "variant"]
    ))

    term_data["terms"] = all_terms

    # Write output
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(term_data, f, ensure_ascii=False, indent=2)

    # Statistics
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"\n  Original terms: {existing_count}")
    print(f"  New terms added: {len(all_new_terms)}")
    print(f"  Total duplicates skipped: {total_duplicates}")
    print(f"  Final total: {len(all_terms)}")
    print(f"\n  Terms without Chinese translation: {zh_none_count}")
    print(f"  Terms without definition: {def_none_count}")

    print("\n  Category Distribution:")
    for cat, count in sorted(cat_counter.items(), key=lambda x: -x[1]):
        pct = count / len(all_terms) * 100
        bar = "#" * int(pct / 2)
        print(f"    {cat}: {count:5d} ({pct:5.1f}%) {bar}")

    print("\n  Source Distribution:")
    for src, count in sorted(source_counter.items(), key=lambda x: -x[1]):
        print(f"    {src}: {count}")

    print(f"\n  Output: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
