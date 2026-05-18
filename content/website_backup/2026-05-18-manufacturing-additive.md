---
title: "增材制造概述"
date: 2026-05-18
draft: false
categories: ["制造工艺"]
tags: ["制造工艺", "增材制造", "机械百科"]
keywords: ["3D打印", "SLM", "FDM", "SLA", "增材材料"]
description: "增材制造（3D打印）是通过逐层堆积材料直接制造三维零件的先进制造技术，区别于传统的切削去除成形，具有设计自由度高、材料利用率高的优势。"
quality: "C"
aliases: ["/p/manufacturing-additive"]
---
# 增材制造概述
> 增材制造（3D打印）是通过逐层堆积材料直接制造三维零件的先进制造技术，区别于传统的切削去除成形，具有设计自由度高、材料利用率高的优势。
<!--more-->
## 概述
增材制造是一种“自下而上”的材料堆积成形技术，通过计算机控制将三维CAD模型切片为二维截面，逐层堆积材料直至形成完整零件。与减材制造相比，增材制造无需专用模具，可制造传统工艺难以实现的复杂内部结构和点阵结构。
## 增材制造工艺分类
金属增材制造主流工艺包括选择性激光熔化[^t4]（SLM）、电子束熔化（EBM）、激光粉末床熔融（LPBF）和定向能量沉积（DED）。非金属增材制造包括熔融沉积成型[^t2]（FDM）、光固化（SLA）和选择性激光烧结（SLS）等。
## 增材制造材料
金属增材制造常用材料有不锈钢（316L、17-4PH）、钛合金（Ti-6Al-4V）、铝合金（AlSi10Mg）、镍基高温合金（Inconel 718）和钴铬合金。高分子增材制造材料包括PLA、ABS、尼龙（PA12）、光敏树脂和高性能聚合物。
## 工艺参数与质量控制
增材制造的关键工艺参数包括激光功率、扫描速度、层厚、扫描策略和预热温度。常见缺陷有气孔、未熔合、变形和表面粗糙度问题。热处理（去应力退火、热等静压HIP）可改善组织致密度和力学性能。
## 应用领域与发展趋势
增材制造在航空航天（轻量化结构件）、医疗器械（定制化植入物）、模具制造（随形冷却水道）和汽车制造（功能原型）领域有重要应用。多材料打印、大尺寸打印和高速打印是当前技术的发展方向。
## 参考数据
下表列出与本节相关的权威工程数据:

- **常用热处理工艺参数**: 退火: 加热Ac₃+30-50°C→炉冷, 正火: 加热Ac₃+30-50°C→空冷 (engineers-edge)
- **焊接工艺参数参考**: 手工电弧焊电流: Φ3.2焊条 100-130A, Φ4.0 140-180A (engineers-edge)
- **切削加工参数**: 车削碳钢: 切削速度 80-150m/min, 进给 0.1-0.3mm/r (engineering-toolbox)
## 总结
增材制造是制造业的革命性技术，在复杂结构制造、个性化定制和快速原型方面具有传统工艺不可比拟的优势。
## 参见
- [3D打印](/p/manufacturing-additive-参见-3D打印/)
- [熔融沉积成型](/p/manufacturing-additive-参见-熔融沉积成型/)
- [光固化成型](/p/manufacturing-additive-参见-光固化成型/)
- [选择性激光熔化](/p/manufacturing-additive-参见-选择性激光熔化/)
- [Branislav Hadzima](/p/manufacturing-additive-参见-Branislav Hadzima/)
- [tesla自动化](/p/manufacturing-additive-参见-tesla自动化/)
- [hookeslaw-强度ofmaterials](/p/manufacturing-additive-参见-hookeslaw-强度ofmaterials/)
- [slab罩设计spreadsheet](/p/manufacturing-additive-参见-slab罩设计spreadsheet/)
- [混凝土](/p/manufacturing-additive-参见-混凝土/)
- [设计](/p/manufacturing-additive-参见-设计/)
- [制造工艺 分类索引](/categories/制造工艺/)


**相关专业术语:** 3D打印[^t1]、熔融沉积成型[^t2]、光固化成型[^t3]、选择性激光熔化[^t4]、Branislav Hadzima[^t5]、tesla自动化[^t6]、hookeslaw-强度ofmaterials[^t7]

---
### 术语注释与数据来源

[^t1]: **3D打印** (3D printing) — 3D printing是一种重要的制造工艺方法，用于金属或非金属材料的加工成型
      来源: seed
[^t2]: **熔融沉积成型** (FDM) — FDM是机械工程领域的重要概念
      来源: seed
[^t3]: **光固化成型** (SLA) — SLA是机械工程领域的重要概念
      来源: seed
[^t4]: **选择性激光熔化** (SLM) — SLM是机械工程领域的重要概念
      来源: seed
[^t5]: **Branislav Hadzima** (Branislav Hadzima) — Branislav Hadzima (born 1976 in Levoča, Slovakia) is a Slovak  mechanical engineer,   materials scientist, and university professor of materials engineering at the University of Žilina. His research f
      来源: wikipedia
[^t6]: **tesla自动化** (Tesla Automation) — Tesla Automation 是机械工程中tesla自动化相关的术语。
      来源: wikipedia
[^t7]: **hookeslaw-强度ofmaterials** (Hookes Law - Strength of Materials) — Hookes Law - Strength (Mechanics) of Materials
Mechanics of Materials Table of Content
- If a metal is lightly stressed, a temporary deformation, presumably permitted by an elastic displacement of the
[^t8]: **桥** (Bridge Concrete Slab Design Spreadsheet) — Ensure that you verify units utilized in excel application meet your requirements before downloading.
      来源: engineers-edge

### 参考资料
- **Engineers Edge**: [Rectangular Concrete Beam and Slab Section Analysis](https://www.engineersedge.com/civil_engineering/concrete_section_analysis/concrete_section_analysis.htm)   — Engineers Edge
- **Engineers Edge**: [Slab Punching Shear Calculation Spreadsheet](https://www.engineersedge.com/civil_engineering/slab_punching_shear_14075.htm)   — Engineers Edge
- **NIST Engineering**: [Opportunity Stanislaus / VOLT Institute | NIST](https://www.nist.gov/mep/centers/opportunity-stanislaus-volt-institute)   — National Institute of Standards and Technology
- **NIST Engineering**: [Growth and Lean Project make positive impact at Grand Slam Safety | NIST](https://www.nist.gov/mep/successstories/2021/growth-and-lean-project-make-positive-impact-grand-slam-safety)   — National Institute of Standards and Technology
- **arXiv Mechanical Engineering**: [Dielectric slab reflection/transmission as a self-consistent radiation phenomenon](http://arxiv.org/abs/1807.05828v1)   — arXiv.org / Cornell University
- **arXiv Mechanical Engineering**: [Control Hardware-in-the-loop for Voltage Controlled Inverters with Unbalanced and Non-linear Loads in Stand-alone Photovoltaic(PV) Islanded Microgrids](http://arxiv.org/abs/2007.05306v3)   — arXiv.org / Cornell University
- [机械工程术语表(英文)](/terminology/)
- [GB/ISO 标准参考](/standards/)

### 延伸阅读
- Wikipedia相关词条

### 外部链接
- [机械工程分类索引](/categories/)
