#!/usr/bin/env python3
"""机械师大百科 AI内容生成管线 — 参考知识库生成网站+公众号版内容"""
import json, re, sys, datetime
from pathlib import Path

BASE = Path(__file__).parent.parent
KB = BASE / "knowledge-base"
CONTENT = BASE / "content"
WEBSITE = CONTENT / "website"
WECHAT = CONTENT / "wechat"
PUBLISHED = CONTENT / "published"

for d in [WEBSITE, WECHAT, PUBLISHED]:
    d.mkdir(parents=True, exist_ok=True)

# Load knowledge base data
def load_kb():
    data = {}
    for f in KB.glob("*.json"):
        try:
            data[f.stem] = json.loads(f.read_text())
        except:
            pass
    return data

# Article templates (10 foundational topics for the mechanical engineering wiki)
ARTICLES = [
    {
        "id": "heat-treatment-intro",
        "title": "热处理概述：退火、正火、淬火与回火",
        "title_en": "Heat Treatment Overview: Annealing, Normalizing, Quenching and Tempering",
        "category": "工程材料",
        "keywords": ["热处理", "退火", "正火", "淬火", "回火", "heat treatment"],
        "tags": ["材料科学", "热处理工艺", "基础概念"],
    },
    {
        "id": "mechanical-properties",
        "title": "力学性能指标解析：强度、硬度、韧性、疲劳",
        "title_en": "Mechanical Properties: Strength, Hardness, Toughness, Fatigue",
        "category": "力学强度",
        "keywords": ["强度", "硬度", "韧性", "疲劳", "力学性能"],
        "tags": ["材料力学", "材料性能", "基础概念"],
    },
    {
        "id": "gear-design-basics",
        "title": "齿轮设计基础：分类、参数与传动原理",
        "title_en": "Gear Design Basics: Classification, Parameters and Transmission Principles",
        "category": "机械设计",
        "keywords": ["齿轮", "传动", "模数", "压力角", "gear"],
        "tags": ["机械设计", "传动系统", "齿轮"],
    },
    {
        "id": "bearing-selection-guide",
        "title": "轴承选型指南：类型、特点与适用场景",
        "title_en": "Bearing Selection Guide: Types, Characteristics and Applications",
        "category": "机械设计",
        "keywords": ["轴承", "ball bearing", "roller bearing", "滑动轴承"],
        "tags": ["机械设计", "轴承", "选型指南"],
    },
    {
        "id": "forging-technology",
        "title": "锻造工艺：自由锻与模锻的技术要点",
        "title_en": "Forging Technology: Key Points of Open Die and Closed Die Forging",
        "category": "制造工艺",
        "keywords": ["锻造", "自由锻", "模锻", "热锻"],
        "tags": ["制造工艺", "锻造", "热模锻"],
    },
    {
        "id": "cnc-machining-intro",
        "title": "数控加工（CNC）基本原理与应用",
        "title_en": "CNC Machining: Principles and Applications",
        "category": "制造工艺",
        "keywords": ["CNC", "数控", "加工中心", "车削", "铣削"],
        "tags": ["制造工艺", "数控加工", "自动化"],
    },
    {
        "id": "fluid-mechanics-basics",
        "title": "流体力学基础：液压与气动系统原理",
        "title_en": "Fluid Mechanics: Principles of Hydraulic and Pneumatic Systems",
        "category": "热工流体",
        "keywords": ["流体力学", "液压", "气动", "伯努利"],
        "tags": ["热工流体", "液压", "气动"],
    },
    {
        "id": "tolerance-gdt",
        "title": "公差与配合：从基本概念到GD&T",
        "title_en": "Tolerance and Fit: From Basics to GD&T",
        "category": "制图CAD",
        "keywords": ["公差", "配合", "GD&T", "尺寸公差"],
        "tags": ["制图", "公差", "GD&T"],
    },
    {
        "id": "mechatronics-sensor-actuator",
        "title": "机电一体化：传感器与执行器概述",
        "title_en": "Mechatronics: Sensors and Actuators Overview",
        "category": "机电自动化",
        "keywords": ["传感器", "执行器", "电机", "PLC", "机器人"],
        "tags": ["机电一体化", "传感器", "执行器", "自动化"],
    },
    {
        "id": "welding-technology",
        "title": "焊接工艺分类与应用指南",
        "title_en": "Welding Processes: Classification and Application Guide",
        "category": "制造工艺",
        "keywords": ["焊接", "电弧焊", "气焊", "激光焊接", "焊接质量"],
        "tags": ["制造工艺", "焊接", "连接工艺"],
    },
]

def get_zh_content(article_id):
    """Return pre-written Chinese content for each article"""
    contents = {
        "heat-treatment-intro": {
            "website_intro": (
                "热处理是机械制造中不可或缺的关键工艺，通过控制金属材料的加热、保温和冷却过程，"
                "改变其内部组织结构，从而获得所需的力学性能和使用性能。本文将系统介绍退火、正火、"
                "淬火与回火四种基本热处理方法。"
            ),
            "sections": [
                ("什么是热处理", (
                    "热处理（Heat Treatment）是指将金属材料在固态下通过加热、保温和冷却的方式，"
                    "使其获得预期组织和性能的工艺方法。热处理的三个基本要素是加热温度、保温时间和冷却速度。"
                    "根据加热和冷却方式的不同，可分为整体热处理、表面热处理和化学热处理三大类。"
                )),
                ("退火（Annealing）", (
                    "退火是将金属加热到一定温度，保持足够时间后缓慢冷却（通常随炉冷却）的热处理工艺。"
                    "目的包括：降低硬度以改善切削加工性、消除残余应力、细化晶粒、均匀化学成分。"
                    "常见的退火工艺有完全退火、球化退火、去应力退火、再结晶退火等。"
                )),
                ("正火（Normalizing）", (
                    "正火是将工件加热到Ac3（或Accm）以上30-50℃，保温后在空气中自然冷却的工艺。"
                    "正火的冷却速度比退火快，得到的组织更细，硬度和强度略高于退火。"
                    "正火常用于碳钢和低合金钢，可作为最终热处理或预备热处理。"
                )),
                ("淬火（Quenching）", (
                    "淬火是将钢加热到相变温度以上，保温后以大于临界冷却速度快速冷却，"
                    "获得马氏体组织的热处理工艺。淬火介质常用水、油、盐水或聚合物溶液。"
                    "淬火能显著提高钢的硬度和耐磨性，但也导致脆性增大和内应力。"
                )),
                ("回火（Tempering）", (
                    "回火是将淬火后的钢重新加热到Ac1以下某温度，保温后冷却的工艺。回火消除或减少淬火内应力，"
                    "稳定组织，调整性能。根据回火温度分为低温回火（150-250℃，获得回火马氏体）、"
                    "中温回火（350-500℃，获得回火屈氏体）和高温回火（500-650℃，获得回火索氏体）。"
                    "淬火+高温回火称为调质处理。"
                )),
            ],
            "summary": (
                "退火、正火、淬火和回火构成了金属热处理的基础四把火。合理选择工艺参数，"
                "可以大幅改善材料的服役性能。在实际生产中，常根据具体零件要求组合使用多种热处理工艺。"
            ),
        },
        "mechanical-properties": {
            "website_intro": (
                "力学性能是选择工程材料最重要的依据之一。本文详细解析强度、硬度、韧性和疲劳"
                "四个核心力学性能指标的定义、测试方法及其工程意义。"
            ),
            "sections": [
                ("强度（Strength）", (
                    "强度是材料抵抗外力作用而不产生过量塑性变形或断裂的能力。\"屈服强度\"指材料开始产生"
                    "明显塑性变形时的应力值，是工程设计中最重要的强度指标之一。\"抗拉强度\"指材料在拉断前"
                    "所能承受的最大应力，衡量材料的极限承载能力。\"抗压强度\"和\"抗剪强度\"则分别对应不同的"
                    "受力方式。"
                )),
                ("硬度（Hardness）", (
                    "硬度是材料抵抗局部变形（特别是压痕）的能力。常用的硬度测试方法包括：洛氏硬度（HRC、HRB），"
                    "通过压入深度差计算硬度值；布氏硬度（HB），通过压痕直径计算；维氏硬度（HV），"
                    "适用于薄层和微观区域。硬度测试简便快速，常作为质量检验的重要手段。"
                )),
                ("韧性（Toughness）", (
                    "韧性是材料在断裂前吸收能量的能力，是强度和塑性的综合表现。高韧性材料在断裂前能"
                    "吸收大量能量，表现为延性断裂；低韧性材料则表现为脆性断裂。冲击韧性常用夏比冲击试验"
                    "测定，断裂韧性（KIC）则反映材料抵抗裂纹扩展的能力。"
                )),
                ("疲劳（Fatigue）", (
                    "疲劳指材料在交变载荷作用下，即使应力低于屈服强度也会发生断裂的现象。"
                    "据统计，机械零件的失效约80%-90%与疲劳有关。疲劳寿命受应力幅值、平均应力、"
                    "表面质量、环境因素等多方面影响。S-N曲线是描述材料疲劳行为的基本工具。"
                )),
            ],
            "summary": (
                "强度、硬度、韧性和疲劳是相互关联又有所区别的力学性能指标。在工程选材和设计中，"
                "需要根据具体工况综合平衡这些性能，才能确保零件安全可靠工作。"
            ),
        },
        "gear-design-basics": {
            "website_intro": (
                "齿轮是最常见的机械传动元件之一，广泛应用于各种机械设备中。"
                "本文系统介绍齿轮的分类、基本参数和传动原理。"
            ),
            "sections": [
                ("齿轮的分类", (
                    "按两轴相对位置分为：平行轴齿轮（直齿轮、斜齿轮、人字齿轮）、相交轴齿轮（直齿锥齿轮、"
                    "螺旋锥齿轮）和交错轴齿轮（蜗杆蜗轮、螺旋齿轮）。按齿廓曲线分为：渐开线齿轮、"
                    "摆线齿轮和圆弧齿轮，其中渐开线齿轮应用最广泛。"
                )),
                ("齿轮基本参数", (
                    "模数（m）是齿轮尺寸计算的基础参数，决定了轮齿的大小。压力角（α）一般为20°。"
                    "齿数（z）、齿顶高系数（ha*）和顶隙系数（c*）共同确定了齿廓几何形状。"
                    "一对齿轮啮合时，它们的模数和压力角必须相等。"
                )),
                ("传动原理与速比", (
                    "齿轮传动比i = n1/n2 = z2/z1，其中n为转速，z为齿数。增速传动i<1，减速传动i>1。"
                    "多级齿轮传动总传动比等于各级传动比的乘积。重合度是衡量齿轮传动平稳性的重要指标，"
                    "重叠系数越大传动越平稳。"
                )),
                ("齿轮材料与热处理", (
                    "常用齿轮材料有：调质钢（40Cr、42CrMo）用于中载齿轮、渗碳钢（20CrMnTi）用于重载齿轮、"
                    "氮化钢（38CrMoAl）用于高精度耐磨齿轮。齿面硬化处理包括高频淬火、渗碳淬火和氮化。"
                )),
            ],
            "summary": (
                "齿轮设计涉及几何参数、材料选择、强度计算和精度等级等多个方面。"
                "合理设计齿轮传动不仅能提高传动效率，还能降低噪声和延长使用寿命。"
            ),
        },
        "bearing-selection-guide": {
            "website_intro": (
                "轴承是支撑旋转轴的精密机械元件，其选型直接影响设备性能和寿命。"
                "本文详述各类轴承的特点、适用场景和选型要点。"
            ),
            "sections": [
                ("滚动轴承的分类", (
                    "滚动轴承按滚动体类型分为球轴承和滚子轴承两大类。球轴承包括深沟球轴承、角接触球轴承、"
                    "调心球轴承等；滚子轴承包括圆柱滚子轴承、圆锥滚子轴承、滚针轴承和调心滚子轴承。"
                    "深沟球轴承适用于高速中载，圆锥滚子轴承可同时承受径向和轴向载荷。"
                )),
                ("滑动轴承", (
                    "滑动轴承依靠润滑膜支撑载荷。根据油膜形成方式分为动压轴承（依靠轴旋转形成油膜）"
                    "和静压轴承（外部供油形成油膜）。滑动轴承适用于重载、高速或冲击载荷场合，"
                    "如大型电机、汽轮机主轴等。"
                )),
                ("轴承选型要点", (
                    "选型考虑因素包括：载荷大小和方向（径向/轴向/联合载荷）、转速、工作温度、"
                    "安装空间、精度要求、润滑方式和成本。选型步骤为：确定轴承类型→选取尺寸系列→"
                    "计算额定寿命→校核静载荷→确定配合与游隙。"
                )),
                ("轴承安装与维护", (
                    "轴承安装需保证清洁、正确施力（通过套圈端面）。配合选择基于载荷类型和大小。"
                    "润滑剂选择：脂润滑适用于中低速、密封要求高的场合；油润滑适用于高速、高温场合。"
                    "定期监测振动和温度可有效预防轴承故障。"
                )),
            ],
            "summary": (
                "轴承选型需要在深入了解工况的基础上，综合考虑承载力、转速、精度和经济性。"
                "正确的选型、安装和维护是保证旋转设备长期可靠运行的关键。"
            ),
        },
        "forging-technology": {
            "website_intro": (
                "锻造是利用锻压设备对金属施加压力，使其产生塑性变形以获得所需锻件的成形方法。"
                "本文系统介绍自由锻和模锻两种主要锻造工艺的技术要点。"
            ),
            "sections": [
                ("自由锻（Open Die Forging）", (
                    "自由锻是在上下砧面之间利用简单通用工具使金属变形的锻造方法。"
                    "适用于单件小批量生产、大型锻件（如大型轴类、环形件）和特重锻件。"
                    "基本工序包括镦粗、拔长、冲孔、弯曲和切断等。自由锻灵活性高但精度较低。"
                )),
                ("模锻（Closed Die Forging）", (
                    "模锻是将加热后的金属坯料放入锻模模膛中加压成形的方法。相较于自由锻，"
                    "模锻精度更高、材料利用率更好、生产效率更高。"
                    "适用于批量生产中小型锻件，如汽车连杆、齿轮毛坯等。"
                )),
                ("锻造温度范围", (
                    "锻造温度范围决定成形质量和模具寿命。钢的始锻温度通常为1050-1250℃（含碳量越低"
                    "始锻温度越高），终锻温度为800-900℃。温度过高导致过热或过烧，温度过低则塑性降低、"
                    "变形抗力增大。精密锻造和温锻则控制在稍低温度范围。"
                )),
                ("现代锻造技术", (
                    "现代锻造技术的发展方向包括：精密锻造（近净成形）、等温锻造、多向模锻、"
                    "辊锻和摆动辗压等。有限元模拟（FEM）技术广泛用于优化锻件设计和工艺参数，"
                    "缩短开发周期。热模锻压力机是批量生产精密锻件的核心设备。"
                )),
            ],
            "summary": (
                "锻造工艺在机械制造中占据重要地位，尤其在承受高载荷的关键零部件制造中不可替代。"
                "自由锻适合大型单件，模锻适合批量中小件，两者互为补充。"
            ),
        },
        "cnc-machining-intro": {
            "website_intro": (
                "数控加工（CNC Machining）是利用数字控制系统驱动机床进行自动化切削加工的技术。"
                "它是现代制造业的核心技术之一，本文介绍其基本原理和典型应用。"
            ),
            "sections": [
                ("CNC工作原理", (
                    "CNC系统由程序输入装置、数控装置、伺服驱动系统和机床本体组成。工作原理为："
                    "将零件加工程序输入数控装置→数控装置插补运算→输出脉冲指令给伺服驱动系统→"
                    "伺服电机驱动工作台/主轴按轨迹运动→完成切削。"
                )),
                ("主要CNC加工类型", (
                    "CNC铣削：用旋转的多刃刀具在工件表面铣削，可加工平面、曲面和沟槽。"
                    "CNC车削：工件旋转、刀具直线进给，加工回转体零件。"
                    "CNC钻削：钻孔、攻丝、镗孔。加工中心（Machining Center）集铣削、钻削、"
                    "攻丝等功能于一体，配备刀库可自动换刀。"
                )),
                ("CNC编程基础", (
                    "常用编程方式：手工编程（G代码格式）、CAM自动编程（如UG/NX、Mastercam、PowerMILL）。"
                    "基本G代码包括：G00快速定位、G01直线插补、G02/G03圆弧插补、"
                    "G81钻孔循环等。坐标系统分为绝对坐标（G90）和增量坐标（G91）。"
                )),
                ("CNC加工工艺参数", (
                    "三要素：切削速度Vc（m/min）、进给速度F（mm/min）和切削深度ap（mm）。"
                    "参数选择依据：工件材料、刀具材料（高速钢/硬质合金/陶瓷/立方氮化硼）、"
                    "机床刚性和表面质量要求。高速切削（HSM）可提高加工效率和表面质量。"
                )),
            ],
            "summary": (
                "CNC加工以其高精度、高效率和自动化优势成为现代机械加工的主流方式。"
                "合理选择工艺参数和刀具路径，可显著提升加工质量和效率。"
            ),
        },
        "fluid-mechanics-basics": {
            "website_intro": (
                "流体力学是研究流体运动规律及其与固体相互作用的学科。液压与气动系统"
                "是流体力学在工程中的重要应用。本文介绍流体力学基础概念及液压气动原理。"
            ),
            "sections": [
                ("流体力学基本概念", (
                    "流体的核心参数：密度ρ、粘度μ（动力粘度）、ν（运动粘度=μ/ρ）。"
                    "流动状态分为层流（Re<2320）和湍流（Re>4000），以雷诺数Re=ρvD/μ判断。"
                    "伯努利方程描述了理想流体沿流线运动时速度、压力和高度之间的关系。"
                )),
                ("液压系统原理", (
                    "液压系统基于帕斯卡原理：密闭液体中压力可等值传递。基本组成：动力元件（液压泵）、"
                    "执行元件（液压缸/马达）、控制元件（各种液压阀）、辅助元件（油箱/管路/滤油器）"
                    "和工作介质（液压油）。液压系统功率密度大、响应快、可实现精确控制。"
                )),
                ("气动系统特点", (
                    "气动系统以压缩空气为介质，相比液压系统工作压力较低（通常0.4-0.8MPa），"
                    "但具有清洁、安全、成本低的特点。基本组成：空气压缩机→后冷却器→储气罐→"
                    "过滤器→调压阀→油雾器→方向阀→气缸。气缸类型有单作用、双作用和旋转气缸。"
                )),
                ("典型应用", (
                    "液压技术广泛应用于工程机械（挖掘机、起重机）、机床（油压机、注塑机）、"
                    "冶金设备。气动技术则多用于自动化生产线、机器人末端执行器、包装设备等。"
                    "电液伺服系统结合了液压的大功率和电子控制的灵活性。"
                )),
            ],
            "summary": (
                "流体力学原理是液压与气动技术的理论基础。液压系统适合大功率精确控制场合，"
                "气动系统在自动化和轻载场合具有独特优势。两者在现代机械中互为补充。"
            ),
        },
        "tolerance-gdt": {
            "website_intro": (
                "公差与配合是机械设计中保证零件互换性和装配质量的基础概念。"
                "本文从尺寸公差、配合制度到GD&T（几何尺寸与公差）进行全面介绍。"
            ),
            "sections": [
                ("尺寸公差基本概念", (
                    "尺寸公差是允许的尺寸变动量。基本尺寸是设计给定的理论尺寸。"
                    "上偏差=最大极限尺寸-基本尺寸，下偏差=最小极限尺寸-基本尺寸。"
                    "公差带由公差大小和位置决定。IT（国际公差）等级从IT01到IT18共20个等级，"
                    "IT6-IT7为精密级，IT8-IT11为中等精度，IT12以下为粗级。"
                )),
                ("配合制度", (
                    "配合指基本尺寸相同的相互结合的孔和轴公差带之间的关系。基孔制（H）和基轴制（h）"
                    "是两种基准制。配合分为三类：间隙配合（孔大于轴）、过盈配合（轴大于孔，"
                    "需压入装配）和过渡配合（可能有间隙或过盈，用于定心要求高的场合）。"
                )),
                ("几何公差（GD&T）", (
                    "GD&T控制零件的形状、方向、位置和跳动误差。形状公差：直线度、平面度、圆度、圆柱度。"
                    "方向公差：平行度、垂直度、倾斜度。位置公差：位置度、同轴度、对称度。"
                    "跳动公差：圆跳动和全跳动。最大实体原则（MMC）可在保证装配的前提下放宽公差。"
                )),
                ("表面粗糙度", (
                    "表面粗糙度是加工表面微观几何形状误差。常用参数：Ra（轮廓算术平均偏差）和Rz"
                    "（微观不平度十点高度）。典型值：精磨Ra0.2-0.8μm，精车Ra1.6-3.2μm，"
                    "粗车Ra6.3-12.5μm。表面粗糙度影响配合性质、疲劳强度和摩擦磨损。"
                )),
            ],
            "summary": (
                "合理的公差设计在保证功能的前提下降低制造成本。GD&T相比传统坐标公差"
                "更能准确表达设计意图，是现代精密制造的基础语言。"
            ),
        },
        "mechatronics-sensor-actuator": {
            "website_intro": (
                "机电一体化（Mechatronics）融合了机械、电子、控制和计算机技术。"
                "传感器和执行器是机电系统的\"感官\"和\"肌肉\"，本文概述其原理和应用。"
            ),
            "sections": [
                ("传感器概述", (
                    "传感器将物理量转换为电信号。分类：位移传感器（光栅尺、编码器）、"
                    "力传感器（应变片、测力传感器）、温度传感器（热电偶、热电阻、红外测温）、"
                    "压力传感器（压阻式、电容式）、流量传感器（涡轮式、电磁式）。"
                )),
                ("执行器概述", (
                    "执行器将电信号转换为机械运动。电机是最常见的执行器：直流电机调速范围宽、"
                    "交流电机结构简单、伺服电机适用于精确位置控制、步进电机适用于开环定位控制。"
                    "液压/气动执行器用于大功率场合。直线电机直接产生直线运动。"
                )),
                ("控制系统架构", (
                    "典型控制系统：传感器→信号调理→A/D转换→控制器（PLC/单片机/DSP）→"
                    "D/A转换→驱动器→执行器→被控对象。反馈回路通过检测输出信号并与设定值比较，"
                    "实现精确控制。PID控制器是最广泛应用的反馈控制算法。"
                )),
                ("工业机器人", (
                    "工业机器人是机电一体化的典型代表。基本组成：机械臂、末端执行器、"
                    "控制器、驱动系统和传感器系统。常见类型包括六轴关节机器人、SCARA机器人、"
                    "并联机器人和协作机器人。广泛应用于焊接、搬运、装配、喷涂等工序。"
                )),
            ],
            "summary": (
                "传感器和执行器是机电一体化系统的核心部件。传感器和执行器、"
                "控制算法的协同配合，实现了机械系统的高精度自动化运行。"
            ),
        },
        "welding-technology": {
            "website_intro": (
                "焊接是通过加热或加压（或两者并用）使工件达到原子结合的一种永久性连接方法。"
                "焊接是金属加工中最重要的连接技术之一，本文介绍主要焊接工艺及其应用。"
            ),
            "sections": [
                ("熔焊工艺", (
                    "电弧焊（SMAW，即手工焊条电弧焊）是最基本的熔焊方法。气体保护焊包括MIG/MAG焊"
                    "（熔化极惰性/活性气体保护焊）和TIG焊（钨极氩弧焊）。埋弧焊（SAW）适合中厚板"
                    "长焊缝自动化焊接。激光焊接能量密度高、热影响区小。"
                )),
                ("压力焊工艺", (
                    "电阻焊通过工件接触面的电阻热加压完成焊接，包括点焊、缝焊和对焊。"
                    "摩擦焊利用摩擦热使端面达到塑性状态后加压。扩散焊在真空或保护气氛中"
                    "通过高温高压使界面原子扩散实现连接。"
                )),
                ("焊接质量控制", (
                    "主要缺陷有裂纹、气孔、夹渣、未熔合和变形等。预防措施包括：焊前预热、"
                    "选择合适焊接参数、控制层间温度、焊后热处理。无损检测方法：超声波检测（UT）、"
                    "射线检测（RT）、磁粉检测（MT）和渗透检测（PT）。"
                )),
                ("焊接材料选择", (
                    "焊条按药皮类型分为酸性焊条（钛钙型）和碱性焊条（低氢型）。"
                    "焊丝选择需与母材匹配。焊接低碳钢常用E43系列焊条。焊接高强钢、"
                    "不锈钢和耐热钢需选用对应的专用焊材。焊剂配合埋弧焊和电渣焊使用。"
                )),
            ],
            "summary": (
                "焊接工艺种类繁多，选择合适的方法和参数是保证焊接质量的关键。"
                "随着自动化焊接和智能化焊接技术的发展，焊接质量和效率持续提升。"
            ),
        },
    }
    return contents.get(article_id)

def generate_hugo_frontmatter(article, content_data):
    """Generate Hugo frontmatter (YAML format)"""
    date = datetime.date.today().isoformat()
    return f"""---
title: "{article['title']}"
date: {date}
draft: false
categories: ["{article['category']}"]
tags: [{', '.join(f'"{t}"' for t in article['tags'])}]
keywords: [{', '.join(f'"{k}"' for k in article['keywords'])}]
description: "{content_data['website_intro']}"
aliases: ["/p/{article['id']}"]
---

"""

def generate_website_content(article, content_data):
    """Generate Hugo Markdown content for website"""
    lines = []
    lines.append(f"# {article['title']}\n")
    lines.append(f"> {content_data['website_intro']}\n")
    lines.append("<!--more-->\n")

    for title, body in content_data['sections']:
        lines.append(f"## {title}\n")
        lines.append(f"{body}\n")

    lines.append("## 总结\n")
    lines.append(f"{content_data['summary']}\n")

    # SEO section
    lines.append("---\n")
    lines.append("### 相关术语\n")
    for kw in article['keywords']:
        lines.append(f"- {kw}\n")

    lines.append("\n### 参考资料\n")
    lines.append("- [English Terminology Reference](/terminology/)\n")
    lines.append("- [GB/ISO Standards Reference](/standards/)\n")

    return "".join(lines)

def generate_wechat_content(article, content_data):
    """Generate WeChat-formatted content (abbreviated)"""
    lines = []
    lines.append(f"{article['title']}\n")
    lines.append("=" * 40 + "\n\n")
    lines.append(f"{content_data['website_intro']}\n\n")

    for title, body in content_data['sections']:
        lines.append(f"▎{title}\n")
        lines.append(f"{body}\n\n")

    lines.append("━" * 30 + "\n")
    lines.append(f"💡 {content_data['summary']}\n\n")
    lines.append("---\n")
    lines.append("📌 这是机械师大百科系列内容，欢迎关注获取更多机械工程知识。\n")

    return "".join(lines)

def main():
    kb = load_kb()
    date_str = datetime.date.today().isoformat()

    generated = 0
    for article in ARTICLES:
        aid = article["id"]
        content_data = get_zh_content(aid)
        if not content_data:
            print(f"  ⏭️ 跳过: {article['title']} (无内容)", file=sys.stderr)
            continue

        # 1. Hugo website version
        hugo_md = generate_hugo_frontmatter(article, content_data)
        hugo_md += generate_website_content(article, content_data)
        wf = WEBSITE / f"{date_str}-{aid}.md"
        wf.write_text(hugo_md)

        # 2. WeChat version
        wx_content = generate_wechat_content(article, content_data)
        wxf = WECHAT / f"{date_str}-{aid}_DRAFT.md"
        wxf.write_text(wx_content)

        generated += 1
        print(f"  ✅ [{generated}] {article['title']}", file=sys.stderr)

    print(f"\n✅ 总计: {generated}/{len(ARTICLES)} 篇", file=sys.stderr)
    print(f"   网站版: {WEBSITE}/", file=sys.stderr)
    print(f"   公众号: {WECHAT}/", file=sys.stderr)

if __name__ == "__main__":
    main()
