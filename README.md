# 机械师大百科 · 六阶段流水线项目

> 双平台（网页站 + 微信公众号）机械工程百科内容项目。
> **六阶段线性流水线：海外采集 → 本地化生成 → 本地建站 → 审校 → 上线 → 公众号**

## 目录结构

```
机械师大百科项目/
├── README.md                   本文件
├── content/                    内容管线（核心）
│   ├── website/                网站版草稿（Hugo Markdown）
│   ├── wechat/                 公众号版草稿（精简版）
│   └── published/              已发布的备份
├── knowledge-base/             知识库（术语表、标准对照、原始语料）
├── scripts/                    自动化脚本
│   ├── generate-content.py     内容生成管线（S1术语注释引擎）
│   ├── hugo2wechat.py          Markdown→公众号格式转换器
│   └── content-workflow.sh     内容审稿发布工作流
├── raw/                        海外采集原始数据（Scrapers 产出）
├── scrapers/                   海外站点批量采集脚本
├── templates/                  文章模板（11类54子类）
├── reviews/                    审核记录
└── kanban-reports/             看板 PM 报告（自动生成）
```

## 流水线（门禁放行制）

```
Phase 1: 海外海量采集 ────────────────────── 门禁: 原始语料库 ≥ 5000条
          ↓ (前序全完成后方可进入Phase 2)
Phase 2: 本地化内容生成 (1000+篇) ────────── 门禁: 质量分 ≥ 7/10
          ↓
Phase 3: 本地网站搭建 (Hugo，不上线) ────── 门禁: 1000+页面无构建错误
          ↓
Phase 4: 线下内容审校 ────────────────────── 门禁: 审校通过放行
          ↓
Phase 5: 上线到服务器 ────────────────────── 全量内容同步+生产监控
          ↓
Phase 6: 公众号运营 ──────────────────────── 持续发布+粉丝增长
```

## 常用命令

```bash
# 1. 生成内容草稿
./scripts/content-workflow.sh generate "热处理工艺分类详解"

# 2. 查看待审清单
./scripts/content-workflow.sh list

# 3. 审核通过
./scripts/content-workflow.sh review 2026-05-17-热处理工艺分类详解_DRAFT.md

# 4. 发布
./scripts/content-workflow.sh publish 2026-05-17-热处理工艺分类详解.md

# 5. 查看管线状态
./scripts/content-workflow.sh status
```

## 看板管理

看板统一使用 Hermes kanban，Web UI (http://127.0.0.1:8787/) → Kanban 面板实时查看。

**v3.0 流水线看板（新）**：
```bash
# 查看 v3.0 流水线任务
hermes kanban --board jixiebaike-v3 list
hermes kanban --board jixiebaike-v3 stats

# 创建/变更
hermes kanban --board jixiebaike-v3 create "标题" --body "描述"
hermes kanban --board jixiebaike-v3 complete <task-id>
hermes kanban --board jixiebaike-v3 block <task-id>
```

**旧看板（存档）**：
```bash
hermes kanban --board jixiebaike list
```

## 任务阶段

| Phase | 名称 | 任务数 | 已完成 | 门禁 |
|-------|------|--------|--------|------|
| A | 海外海量采集 | 16 | 5 | 原始语料库 ≥ 5000 条 |
| B | 本地化内容生成 (1000+篇) | 12 | 3 | 质量分 ≥ 7/10 |
| C | 本地网站搭建 | 8 | 2 | 本地 0 错误 |
| D | 线下内容审校 | 7 | 0 | 审校全部放行 |
| E | 上线到服务器 | 9 | 2 | 全量健康检查通过 |
| F | 公众号运营 | 8 | 1 | — |

## 里程碑

| 里程碑 | 条件 | 说明 |
|--------|------|------|
| M1: 语料就绪 | Phase A 100% | 海外原始资料 ≥ 5000 条 |
| M2: 千篇产出 | Phase B 100% | 1000+ 篇本地化百科 |
| M3: 线下就绪 | Phase C+D 100% | 网站可本地访问，全部审核通过 |
| M4: 上线运行 | Phase E 100% | 生产环境可用 |
| M5: 公众号开张 | Phase F 100% | 公众号持续运营 |

## 内容质量标准

### 规则 S1：术语注释与来源 — 全局强制标准

每篇百科词条必须满足以下两个条件，缺一不可：

1. **术语注释** — 文中出现的每个专业名词（术语）必须有对应的词条注释（术语定义或简要解释），首次出现时标注
2. **来源引用** — 每个术语注释必须附带明确的数据来源说明

### 标注格式

**网站版 (Hugo Markdown)** — 使用脚注（footnote）格式：
```markdown
淬火（Quenching）是将钢加热到相变温度以上快速冷却以获得马氏体[^m]组织的工艺。
[^m]: **马氏体** — 碳在α-Fe中的过饱和固溶体，硬度高、脆性大
       **来源**: 机械工程术语表 v2 (knowledge-base/mech-terminology-v2.json)
       **参阅**: GB/T 7232-2023 金属热处理术语
```

**微信公众号版** — 使用 ※ 标记 + 文末来源说明：
```markdown
淬火（Quenching）是将钢加热到相变温度以上快速冷却以获得马氏体※组织的工艺。

※数据来源:
· 马氏体 — 机械工程术语表 v2
· 淬火热处理参数 — GB/T 7232-2023 金属热处理术语
```

### 规则 S2：来源优先级

术语注释的数据来源按以下优先级选取：
1. **GB/ISO 标准** — 有国家/国际标准的术语优先引用标准号（如 GB/T 7232-2023）
2. **机械工程术语表** — 项目知识库 `mech-terminology-v2.json`（645条核心术语）
3. **MIT OCW 教材** — `knowledge-base/mit-ocw-courses.json`（74门ME课程）
4. **Wikipedia** — `knowledge-base/wikipedia-pages.json`（400英文词条）

### 规则 S3：注释密度要求

- 每篇词条（约 800-1500 字）至少标注 **5 个核心术语**
- 每个章节至少 **1 个术语注释**
- 术语首次出现时标注，后续重复出现不再标注

### 执行

- `scripts/generate-content.py` 自动为每篇词条添加术语脚注和来源列表
- 人工审稿时检查注释准确性和来源完整性
- HTML 项目看板中新增"术语注释覆盖率"指标

## 项目来源

基于 jixiebaike-dual-checklist.html 双平台需求清单，67条需求 + 44项任务。
