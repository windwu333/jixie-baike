# 机械师大百科 · 长期项目文件夹

> 双平台（网页站 + 微信公众号）内容项目。
> 本地生成 → 人工审稿 → 发布上线。

## 目录结构

```
机械师大百科项目/
├── README.md                   本文件
├── content/                    内容管线（核心）
│   ├── website/                网站版草稿（Hugo Markdown）
│   ├── wechat/                 公众号版草稿（精简版）
│   └── published/              已发布的备份
├── knowledge-base/             知识库（术语表、标准对照）
├── scripts/                    自动化脚本
│   └── content-workflow.sh     内容生成→审稿→发布工作流
├── reviews/                    审核记录
└── kanban-reports/             看板 PM 报告（自动生成）
```

## 内容工作流

```
┌─────────────────────────────────────────────────────────┐
│  Step 1: AI 本地生成草稿 → content/website/*_DRAFT.md  │
│                         → content/wechat/*_DRAFT.md     │
├─────────────────────────────────────────────────────────┤
│  Step 2: 你审稿 → content-workflow.sh review <文件>     │
│            审稿通过则去掉 _DRAFT 后缀                    │
├─────────────────────────────────────────────────────────┤
│  Step 3: 发布 → content-workflow.sh publish <文件>      │
│            网站版 → git push → CDN 自动部署             │
│            公众号版 → 复制到公众号后台发布               │
└─────────────────────────────────────────────────────────┘
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

```bash
# 查看所有任务
hermes kanban --board jixiebaike list

# 查看统计
hermes kanban --board jixiebaike stats

# 创建任务
hermes kanban --board jixiebaike create "标题" --body "描述"

# 变更状态
hermes kanban --board jixiebaike complete <task-id>   # 完成
hermes kanban --board jixiebaike block <task-id>      # 阻塞
```

## 任务阶段

| Phase | 时间 | 任务 | 目标 |
|-------|------|------|------|
| Week 1 | 第1周 | T1-T15 (15项) | 网站基建 + 公众号注册 |
| Week 2-3 | 第2-3周 | T16-T25 (10项) | AI管线 + 知识库 + 主题 |
| Week 5-8 | 第5-8周 | T26-T31 (6项) | 日更启动 + 公众号开更 |
| Week 9-24 | 第9-24周 | T32-T37 (6项) | 内容扩张 + 私域积累 |
| Week 25-36 | 第25-36周 | T38-T41 (4项) | 变现启动 |
| Week 37-52 | 第37-52周 | T42-T44 (3项) | Phase 3 决策 |

## 里程碑

| 里程碑 | 时间 | 标准 | 门禁 |
|--------|------|------|------|
| M1: 基建就绪 | 第1周 | 域名+CDN+CI/CD+公众号 | — |
| M2: AI管线V1 | 第4周 | 10条质量≥7/10 | ⛔不达标不放行 |
| M3: 100条 | 第8周 | 网站100条+公众号30条 | — |
| M5: Phase 2a | 第24周 | 1k条+200公众号+500粉 | 决定是否变现 |
| M6: Phase 3 | 第52周 | 1.8k条+300公众号 | 决定是否全职 |

## 项目来源

基于 jixiebaike-dual-checklist.html 双平台需求清单，67条需求 + 44项任务。
