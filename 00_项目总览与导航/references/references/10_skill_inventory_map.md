# 10_skill_inventory_map — 可用 Skill 清单

> 最后更新: 2026-07-13
> 仅列出实际安装的 skill（`<LOCAL_PATH>`），不包含外部/未安装的。

## 科研核心 Skills (4个)

| Skill | 用途 | 频率 |
|-------|------|------|
| `pdf-image-text-extractor` | PDF/图片文本提取（7引擎级联），论文阅读第一步 | 每次论文阅读必用 |
| `academic-paper-writing` | 学术论文写作 | 后期使用 |
| `scientific-figure` | 科学图表设计规范、制图审查 | 作图时使用 |
| `group-meeting-ppt` | 组会PPT生成 | 组会前使用 |

## 开发与工具 Skills (4个)

| Skill | 用途 |
|-------|------|
| `dev-discipline` | 代码/项目/脚本开发纪律 |
| `self-improving-agent` | Agent 自我改进 |
| `memory-manager` | 记忆管理 |
| `skill-creater` | 创建新 Skill |

## PPT Skills (2个)

| Skill | 用途 |
|-------|------|
| `ppt1` | PPT生成方案1 |
| `ppt2` | PPT生成方案2 |

## UI/样式 Skills (2个)

| Skill | 用途 |
|-------|------|
| `ui-styling` | UI样式 |
| `ui-ux-pro-max` | 高级UI/UX |

## 其他 (1个)

| Skill | 用途 |
|-------|------|
| `-ai` | AI相关辅助 |

## 系统内置 Skills (通过 `/` 调用)

| Skill | 用途 |
|-------|------|
| `deep-research` | 深度研究（多源搜索→验证→综合报告） |
| `dataviz` | 数据可视化 |
| `verify` | 代码变更验证 |
| `code-review` | 代码审查 |
| `simplify` | 代码简化 |
| `loop` | 定时循环任务 |

## academic-workflow 实际 skill 使用映射

| 科研环节 | 使用的 Skill |
|----------|-------------|
| PDF文本提取 | `pdf-image-text-extractor` |
| 论文精读 | Claude Sub-Agent（无独立 skill） |
| 知识卡片生成 | Claude 直接生成（按 SKILL.md 模板） |
| 图表分析 | Claude + `scientific-figure` |
| 学术写作 | `academic-paper-writing` |
| 组会PPT | `group-meeting-ppt` |
| 代码/脚本 | `dev-discipline` |
| 深度研究 | `deep-research`（系统内置） |
