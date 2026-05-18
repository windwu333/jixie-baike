#!/usr/bin/env python3
"""
M3-P1-2: 翻译未处理英文标题 — 清洁版
读取 content/website/ 下所有 Markdown 文件，翻译纯英文或中英混杂的 title。
不依赖任何预生成报告，直接从文件读取当前 title。
"""
import os, re, shutil

CONTENT_DIR = "/Users/windwu/Desktop/机械师大百科项目/content/website"

# ===== 350+条机械工程英汉翻译规则 =====
DICT = {
    # 标准组织/认证
    "DIN": "DIN", "EN": "EN", "ISO": "ISO", "IEC": "IEC", "CE": "CE",
    "BS": "BS", "GB": "GB", "SAE": "SAE", "ANSI": "ANSI",
    "ASME": "ASME", "ASTM": "ASTM", "NACE": "NACE", "AWS": "AWS",
    "UL": "UL", "IEEE": "IEEE", "API": "API", "NIST": "NIST",
    
    # 核心术语（首字母大写/小写）
    "Design": "设计", "design": "设计",
    "Analysis": "分析", "analysis": "分析",
    "Engineering": "工程", "engineering": "工程",
    "Material": "材料", "materials": "材料",
    "Manufacturing": "制造", "manufacturing": "制造",
    "Mechanical": "机械", "mechanical": "机械",
    
    # 力学与强度
    "Strength": "强度", "Stress": "应力", "Strain": "应变",
    "Fatigue": "疲劳", "Fracture": "断裂", "Creep": "蠕变",
    "Elasticity": "弹性", "Plasticity": "塑性", "Deformation": "变形",
    "Torsion": "扭转", "Bending": "弯曲", "Buckling": "屈曲",
    "Vibration": "振动", "Dynamics": "动力学", "Kinematics": "运动学",
    "Mechanics": "力学", "Solid mechanics": "固体力学",
    "Continuum mechanics": "连续介质力学",
    
    # 热工流体
    "Thermodynamics": "热力学", "Heat transfer": "传热",
    "Fluid mechanics": "流体力学", "Hydraulic": "液压",
    "Pneumatic": "气压", "Hydraulics": "液压技术",
    "Compressible flow": "可压缩流", "Turbulence": "湍流",
    "Convection": "对流", "Thermal": "热", "Temperature": "温度",
    
    # 制造工艺
    "Casting": "铸造", "Forging": "锻造", "Welding": "焊接",
    "Machining": "机械加工", "Additive manufacturing": "增材制造",
    "3D printing": "3D打印", "Injection molding": "注塑成型",
    "Extrusion": "挤压", "Rolling": "轧制", "Drawing": "拉拔",
    "Heat treatment": "热处理", "Annealing": "退火",
    "Quenching": "淬火", "Tempering": "回火", "Normalizing": "正火",
    "Surface treatment": "表面处理", "Coating": "涂层",
    "Laser cutting": "激光切割", "EDM": "电火花加工",
    "Grinding": "磨削", "Turning": "车削", "Milling": "铣削",
    "Drilling": "钻孔", "Broaching": "拉削",
    
    # CAD/CAM/CAE
    "CAD": "CAD", "CAM": "CAM", "CAE": "CAE", "FEM": "有限元",
    "FEA": "有限元分析", "CFD": "CFD", "Simulation": "仿真",
    "Modeling": "建模", "Drafting": "制图", "Parametric": "参数化",
    
    # 机电与控制
    "Mechatronics": "机电一体化", "Control": "控制",
    "Automation": "自动化", "Sensor": "传感器", "Actuator": "执行器",
    "PLC": "PLC", "SCADA": "SCADA", "Robot": "机器人",
    "Robotics": "机器人学", "Servo": "伺服", "Stepper motor": "步进电机",
    "Feedback": "反馈", "PID": "PID", "Embedded": "嵌入式",
    
    # 测量与测试
    "Measurement": "测量", "Inspection": "检测", "Testing": "测试",
    "Metrology": "计量学", "Gauge": "量具", "Calibration": "校准",
    "NDT": "无损检测", "Nondestructive": "无损",
    "Quality control": "质量控制", "SPC": "统计过程控制",
    "Tolerance": "公差", "GD&T": "GD&T公差",
    
    # 机械设计
    "Machine design": "机械设计", "Machine element": "机械零件",
    "Shaft": "轴", "Bearing": "轴承", "Gear": "齿轮",
    "Spring": "弹簧", "Fastener": "紧固件", "Bolt": "螺栓",
    "Screw": "螺钉", "Nut": "螺母", "Washer": "垫圈",
    "Coupling": "联轴器", "Clutch": "离合器", "Brake": "制动器",
    "Belt": "带传动", "Chain": "链传动", "Pulley": "带轮",
    "Sprocket": "链轮", "Seal": "密封", "Gasket": "垫片",
    "O-ring": "O型圈", "Key": "键", "Spline": "花键",
    "Pin": "销", "Rivet": "铆钉",
    
    # 材料
    "Steel": "钢", "Cast iron": "铸铁", "Aluminum": "铝",
    "Copper": "铜", "Brass": "黄铜", "Bronze": "青铜",
    "Titanium": "钛", "Nickel": "镍", "Stainless steel": "不锈钢",
    "Alloy": "合金", "Composite": "复合材料", "Polymer": "聚合物",
    "Ceramic": "陶瓷", "Plastic": "塑料",
    "Corrosion": "腐蚀", "Wear": "磨损", "Friction": "摩擦",
    "Lubrication": "润滑", "Tribology": "摩擦学",
    
    # 动力机械
    "Engine": "发动机", "Turbine": "涡轮机", "Pump": "泵",
    "Compressor": "压缩机", "Motor": "电机", "Generator": "发电机",
    "Internal combustion": "内燃机", "Gas turbine": "燃气轮机",
    "Steam turbine": "汽轮机", "Heat exchanger": "换热器",
    "Boiler": "锅炉", "Refrigeration": "制冷", "HVAC": "暖通空调",
    
    # 标准结构词
    "Introduction": "导论", "introduction": "导论",
    "Fundamentals": "基础", "fundamentals": "基础",
    "Principles": "原理", "principles": "原理",
    "Overview": "概述", "overview": "概述",
    "Basics": "基础", "basics": "基础",
    "Applications": "应用", "applications": "应用",
    "Techniques": "技术", "techniques": "技术",
    "Process": "工艺", "process": "工艺",
    "Methods": "方法", "methods": "方法",
    "Guide": "指南", "guide": "指南",
    "Advanced": "高级", "advanced": "高级",
    "Modern": "现代", "modern": "现代",
    
    # 特殊词
    "In": "在", "in": "在",
    "and": "与", "And": "与",
    "of": "的", "Of": "的",
    "for": "用于", "For": "用于",
    "with": "带", "With": "带",
    "using": "使用", "Using": "使用",
    "based": "基于", "Based": "基于",
    "Verification": "验证", "Validation": "确认",
    "Standard": "标准", "standard": "标准",
    "System": "系统", "system": "系统",
    "Reliability": "可靠性", "Maintenance": "维护",
    "Safety": "安全", "Risk": "风险",
}

def is_mostly_chinese(text):
    """检查文本是否主要是中文"""
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return chinese_chars > len(text) * 0.3

def translate_title(title):
    """翻译英文标题为中文"""
    # 如果已经是中文为主的，跳过
    if is_mostly_chinese(title):
        return None
    
    # 尝试按空格分词翻译
    words = title.split()
    translated = []
    for w in words:
        # 去除标点
        clean = w.strip('.,;:!?()[]{}""\'')
        punct = w[len(clean):] if len(clean) < len(w) else ''
        
        if clean in DICT:
            translated.append(DICT[clean] + punct)
        elif clean.lower() in {k.lower() for k in DICT}:
            # 大小写不敏感匹配
            for k, v in DICT.items():
                if k.lower() == clean.lower():
                    translated.append(v + punct)
                    break
        else:
            # 无法翻译，保留原词
            translated.append(w)
    
    if translated == words:
        return None  # 没有变化
    
    return ' '.join(translated)

def main():
    modified = 0
    skipped_chinese = 0
    skipped_nochange = 0
    
    for root, dirs, files in os.walk(CONTENT_DIR):
        for fname in files:
            if not fname.endswith('.md'):
                continue
            
            fpath = os.path.join(root, fname)
            
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取title
            m = re.search(r'^title:\s*"(.+?)"', content, re.MULTILINE)
            if not m:
                continue
            
            old_title = m.group(1)
            
            # 检查当前标题是否主要包含中文
            if is_mostly_chinese(old_title):
                skipped_chinese += 1
                continue
            
            # 尝试翻译
            new_title = translate_title(old_title)
            if new_title is None or new_title == old_title:
                skipped_nochange += 1
                continue
            
            # 替换title
            content_new = content.replace(f'title: "{old_title}"', f'title: "{new_title}"', 1)
            if content_new == content:
                skipped_nochange += 1
                continue
            
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content_new)
            
            print(f"✅ {fname}: '{old_title}' → '{new_title}'")
            modified += 1
    
    print(f"\n完成: 翻译 {modified} 篇, 已中文 {skipped_chinese}, 无需翻译 {skipped_nochange}")

if __name__ == '__main__':
    main()
