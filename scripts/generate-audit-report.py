#!/usr/bin/env python3
"""Generate comprehensive Wikipedia framework audit report as HTML"""
import json, re
from pathlib import Path
from datetime import date

REPORTS = Path(__file__).parent.parent / "reports"
AUDIT_JSON = REPORTS / "wiki-framework-audit-report.json"
BASE = Path(__file__).parent.parent
CONTENT = BASE / "content" / "website"

data = json.loads(AUDIT_JSON.read_bytes())
n = data["n"]
checks = data["checks"]

# Count articles with {{name}} template residue
template_residue = 0
for f in sorted(CONTENT.glob("*.md")):
    text = f.read_text()
    if "{{name}}" in text:
        template_residue += 1

# Count articles with English-only titles (no Chinese in title field)
untranslated_titles = 0
for f in sorted(CONTENT.glob("*.md")):
    text = f.read_text()
    m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', text, re.MULTILINE)
    if m:
        title = m.group(1)
        if not re.search(r'[一-鿿]', title):
            untranslated_titles += 1

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wikipedia 框架合规审计报告 · 机械师大百科</title>
<style>
:root{{--bg:#f8f9fa;--surface:#fff;--text:#202122;--text2:#54595d;--accent:#3366cc;--border:#c8ccd1;--green:#14866d;--orange:#e8732a;--red:#d73333}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,'Noto Sans SC','PingFang SC',sans-serif;background:var(--bg);color:var(--text);line-height:1.7;padding:2rem}}
h1{{font-size:1.8rem;margin-bottom:.3rem}}
.subtitle{{color:var(--text2);font-size:.95rem;margin-bottom:1.5rem}}
.section{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1.5rem;margin:1.2rem 0}}
.section h2{{font-size:1.3rem;color:var(--accent);border-bottom:1px solid var(--border);padding-bottom:.5rem;margin-bottom:1rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:.8rem;margin:1rem 0}}
.card{{background:#f0f2f5;border-radius:8px;padding:1rem;text-align:center}}
.card .num{{font-size:2rem;font-weight:700;color:var(--accent)}}
.card .label{{font-size:.8rem;color:var(--text2)}}
.good{{color:var(--green)}}
.warn{{color:var(--orange)}}
.bad{{color:var(--red)}}
table{{width:100%;border-collapse:collapse;font-size:.88rem;margin:.8rem 0}}
th,td{{border:1px solid var(--border);padding:.5rem .7rem;text-align:left;vertical-align:top}}
th{{background:#f0f0f0;font-weight:600}}
tr:nth-child(even) td{{background:#fafafa}}
.bar-wrap{{display:flex;align-items:center;gap:6px;margin:3px 0}}
.bar{{height:18px;border-radius:4px;min-width:4px;transition:width .3s}}
.tag{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.75rem;font-weight:600;color:#fff}}
.tag-crit{{background:#d73333}}
.tag-high{{background:#e8732a}}
.tag-med{{background:#e9c46a;color:#333}}
.collapse summary{{cursor:pointer;font-weight:600;padding:.3rem 0;color:var(--accent)}}
.collapse[open] summary{{margin-bottom:.5rem}}
@media(max-width:640px){{.grid{{grid-template-columns:repeat(2,1fr)}}body{{padding:1rem}}}}
</style>
</head>
<body>

<h1>🔍 Wikipedia 框架合规审计报告</h1>
<p class="subtitle">机械师大百科 · {date.today().isoformat()} · 基础扫描+扩展检测+深度抽样</p>

<div class="section">
  <h2>📊 总览</h2>
  <div class="grid">
    <div class="card"><div class="num">{n}</div><div class="label">总文章数</div></div>
    <div class="card"><div class="num" style="color:var(--green)">{checks['lead_definition']['pct']:.0f}%</div><div class="label">导言定义式 ✅</div></div>
    <div class="card"><div class="num" style="color:var(--green)">{checks['has_references']['pct']:.0f}%</div><div class="label">引用覆盖 ✅</div></div>
    <div class="card"><div class="num" style="color:var(--green)">{checks['no_heading_jumps']['pct']:.0f}%</div><div class="label">标题无跳级 ✅</div></div>
    <div class="card"><div class="num" style="color:var(--orange)">310</div><div class="label">含人称代词 ⚠️</div></div>
    <div class="card"><div class="num" style="color:var(--red)">{template_residue}</div><div class="label">模板残留  {{ '🚨' if template_residue > 0 else '✅' }}</div></div>
    <div class="card"><div class="num" style="color:var(--red)">{untranslated_titles}</div><div class="label">未翻译标题 🚨</div></div>
    <div class="card"><div class="num" style="color:var(--red)">18/20</div><div class="label">样章内容失配</div></div>
  </div>
</div>

<div class="section">
  <h2>✅ 基础合规（S2 扫描 — 2271 篇全量）</h2>
  <table>
    <tr><th>检查项</th><th>通过率</th><th>状态</th></tr>
    <tr><td>R1 导言首句定义式</td><td>{checks['lead_definition']['pct']:.1f}%</td><td class="good">✅</td></tr>
    <tr><td>R1 导言 1-4 段</td><td>{checks['lead_1_4_paras']['pct']:.1f}%</td><td class="good">✅</td></tr>
    <tr><td>R2 标题层级无跳跃</td><td>{checks['no_heading_jumps']['pct']:.1f}%</td><td class="good">✅</td></tr>
    <tr><td>R4 章节长度适当</td><td>{checks['reasonable_section_length']['pct']:.1f}%</td><td class="good">✅</td></tr>
    <tr><td>R5 无时间敏感词</td><td>100.0%</td><td class="good">✅ (S2)</td></tr>
    <tr><td>R9 引用覆盖 (≥1)</td><td>{checks['has_references']['pct']:.1f}%</td><td class="good">✅</td></tr>
    <tr><td>R10 分类标签</td><td>{checks['has_category']['pct']:.1f}%</td><td class="good">✅</td></tr>
    <tr><td>质量分级字段</td><td>{checks['has_quality']['pct']:.1f}%</td><td class="good">✅</td></tr>
  </table>
</div>

<div class="section">
  <h2>⚠️ 结构问题（扩展扫描）</h2>
  <table>
    <tr><th>问题</th><th>数量</th><th>占比</th><th>严重度</th></tr>
    <tr><td>含人称代词 (R7)</td><td>{data['personal_pronoun_issues']}</td><td>{data['personal_pronoun_issues']/n*100:.1f}%</td><td class="warn">MEDIUM</td></tr>
    <tr><td>模板残留 `{{{{name}}}}` 未替换</td><td>{template_residue}</td><td>{template_residue/n*100:.1f}%</td><td class="bad">HIGH</td></tr>
    <tr><td>标题纯英文/中英混杂</td><td>{untranslated_titles}</td><td>{untranslated_titles/n*100:.1f}%</td><td class="bad">HIGH</td></tr>
    <tr><td>加粗过多 (R1)</td><td>{data['bold_issues']}+</td><td>-</td><td class="warn">MEDIUM</td></tr>
    <tr><td>导言段落数异常</td><td>{data['lead_para_issues']}</td><td>{data['lead_para_issues']/n*100:.1f}%</td><td class="warn">LOW</td></tr>
  </table>

  <details class="collapse">
    <summary>📋 含人称代词文章示例（前10篇）</summary>
    <p style="font-size:.82rem;color:var(--text2)">主要是 "we" / "you" 在技术描述中的使用</p>
    <!-- dynamically populated -->
  </details>
</div>

<div class="section">
  <h2>🚨 深度抽样发现（20篇样章）</h2>
  <p style="color:var(--red);font-weight:600">核心问题：类别级模板填充主题级标题 → 标题与内容严重脱节</p>

  <h3>评分分布</h3>
  <div class="grid">
    <div class="card"><div class="num" style="color:var(--red)">1-2分</div><div class="label">严重问题 — 14篇</div></div>
    <div class="card"><div class="num" style="color:var(--orange)">3-4分</div><div class="label">需改进 — 5篇</div></div>
    <div class="card"><div class="num" style="color:var(--green)">6分</div><div class="label">合格 — 1篇</div></div>
  </div>

  <details class="collapse">
    <summary>🔴 CRITICAL 问题（影响 15-18 篇）</summary>
    <ol style="margin:.5rem 0 0 1.5rem">
      <li><strong>标题与内容完全不匹配</strong> — 标题"参数化设计"→内容为制图标准；标题"压力机"→内容为发动机泵；标题"钨"→内容为钢铁；标题"洛氏硬度测试"→内容为有限元分析。文章使用类别级通用模板，未针对具体主题生成专属内容。</li>
      <li><strong>AI生成乱码术语</strong> — 术语表出现 URL 标题被当作术语（如"梁挠度and应力equationscalculatorandformulasfora梁"），来源名被直接抄入术语定义。</li>
      <li><strong>NASA 论文灌水引用</strong> — 几乎所有文章（~99%）引用 6 篇 NASA NTRS 论文，与文章主题无关。仅 measurement-gdt-k1-v 使用了专业相关引用。</li>
      <li><strong>模板残留</strong> — `{{{{name}}}}` 未替换，出现在章节标题中。</li>
      <li><strong>未翻译英文标题</strong> — 标题保留英文/中英混杂（"integrated制造database" / "rockwell hardness test" / "hvac系统"）。</li>
    </ol>
  </details>

  <details class="collapse">
    <summary>🟠 HIGH 问题</summary>
    <ol style="margin:.5rem 0 0 1.5rem">
      <li><strong>同类别文章内容重复</strong> — 同类文章共用同一模板，仅标题不同。制造类4篇(CNC/增材/机加工/焊接)共用模板；CAD类2篇(3D/基准标注)共用模板。</li>
      <li><strong>导言非严格定义式</strong> — 导言首句为通用描述（"是机械设计中的重要组成部分"），非对主题的严格定义。</li>
      <li><strong>参考数据跨类别乱入</strong> — 参考数据节反复出现齿轮强度/轴承寿命/螺栓预紧力等跨类别数据，与文章主题无关。</li>
      <li><strong>参见含乱码链接</strong> — URL片段/半翻译标题作为超链接指向不存在的页面。</li>
    </ol>
  </details>
</div>

<div class="section">
  <h2>📊 质量分级分布</h2>
  <table>
    <tr><th>等级</th><th>篇数</th><th>占比</th><th>分布</th></tr>"""

ql_dist = data.get("quality_distribution", {})
for ql in ["S", "A", "B", "C", "Start", "Draft"]:
    if ql in ql_dist:
        count = ql_dist[ql]
        pct = count / n * 100
        bar_w = max(4, int(pct * 2.5))
        color = {"S": "#14866d", "A": "#2a9d8f", "B": "#e9c46a", "C": "#f4a261", "Start": "#e76f51", "Draft": "#c1121f"}.get(ql, "#999")
        html += f"""<tr><td>{ql}</td><td>{count}</td><td>{pct:.1f}%</td><td><div class="bar-wrap"><div class="bar" style="width:{bar_w}px;background:{color}"></div>{pct:.1f}%</div></td></tr>"""

html += f"""  </table>
  <p style="font-size:.82rem;color:var(--text2);margin-top:.5rem">⚠️ 注意：quality 字段与文章实际内容质量严重脱节。例如 "C" 级文章标题与内容完全无关。</p>
</div>

<div class="section">
  <h2>🎯 根因分析</h2>
  <p>现有生成管线（<code>generate-content-v2.py</code>）的工作方式是<strong>类别级模板 → 填充各类别共用的参考数据和术语</strong>。具体流程：</p>
  <ol style="margin:.5rem 0 0 1.5rem">
    <li>基于类别（如"制造工艺"）加载通用模板</li>
    <li>填充该类别的通用参考数据（齿轮/轴承/螺栓等）</li>
    <li>注入随机选取的 NASA NTRS 论文作为引用</li>
    <li>术语表从术语库按类别提取</li>
  </ol>
  <p>这导致：<strong>同一类别下的所有文章内容几乎相同</strong>，只有标题和少量关键词不同。Wikipedia 框架要求"每个主题独立撰写"（树状分解 R4），非"模板批量填充"。</p>
</div>

<div class="section">
  <h2>📋 推荐改进路线</h2>
  <table>
    <tr><th>优先级</th><th>改进项</th><th>影响范围</th><th>预估工时</th></tr>
    <tr><td><span class="tag tag-crit">P0</span></td><td>修复标题与内容脱节：管线改为按主题（而非类别）生成内容，为每个主题注入专属的参考数据和术语</td><td>2271篇全量</td><td>2-3天</td></tr>
    <tr><td><span class="tag tag-crit">P0</span></td><td>替换无关 NASA 引用为真实相关来源：为每个类别配置专属源（如焊接用AWS标准、CAD用ISO标准）</td><td>~2200篇</td><td>1-2天</td></tr>
    <tr><td><span class="tag tag-high">P1</span></td><td>清理模板残留和乱码术语：批量替换 {{name}}，过滤 URI 片段式术语</td><td>全量+术语表</td><td>0.5天</td></tr>
    <tr><td><span class="tag tag-high">P1</span></td><td>翻译未处理英文标题：对纯英文/中英混杂标题进行翻译</td><td>~200篇</td><td>0.5天</td></tr>
    <tr><td><span class="tag tag-high">P1</span></td><td>消除人称代词：批量替换 "we"/"you" → "可" / 被动语态</td><td>310篇</td><td>0.5天</td></tr>
    <tr><td><span class="tag tag-med">P2</span></td><td>导言优化：将通用描述改为严格定义式（"XX是[分类]的[定义]"）</td><td>2271篇</td><td>1天</td></tr>
    <tr><td><span class="tag tag-med">P2</span></td><td>加粗规范化：仅保留首句一次加粗</td><td>2271篇</td><td>0.5天</td></tr>
    <tr><td><span class="tag tag-med">P2</span></td><td>参考数据按主题筛选：停止跨类别灌入无关数据</td><td>管线配置</td><td>0.5天</td></tr>
  </table>
</div>

<div class="section">
  <h2>📈 与 M2 计划的关系</h2>
  <p>M2 计划（Wikipedia 标准化）已完成的 Phase 1-4 主要覆盖<strong>结构性合规</strong>：</p>
  <ul>
    <li>✅ 导言定义式 — 100%</li>
    <li>✅ 附录顺序 — 100%</li>
    <li>✅ 无时间敏感词 — 100%</li>
    <li>✅ 质量分级字段 — 100%</li>
    <li>✅ 导航/分类 — 100%</li>
  </ul>
  <p style="color:var(--red);font-weight:600">但发现了结构性合规未能覆盖的深层内容质量问题。建议启动 <strong>M3 内容质量改进</strong> 阶段：</p>
  <ul>
    <li>M3 Phase 1: 修复生成管线 — 主题级内容专属生成</li>
    <li>M3 Phase 2: 清理乱码/模板残留</li>
    <li>M3 Phase 3: 引用源专业化</li>
    <li>M3 Phase 4: 全量重新生成 + 内容级合规扫描</li>
  </ul>
</div>

<footer style="margin-top:2rem;font-size:.8rem;color:var(--text2);border-top:1px solid var(--border);padding-top:1rem">
  <p>Generated by Claude Code · {date.today().isoformat()} · S2 扫描 + 扩展审计 + 深度抽样 20 篇</p>
</footer>

</body>
</html>"""

report_path = REPORTS / f"wiki-framework-audit-{date.today().isoformat()}.html"
report_path.write_text(html, encoding="utf-8")
print(f"Report saved: {report_path}")
print(f"Size: {len(html)} bytes")
