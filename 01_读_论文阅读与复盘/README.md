# 01 读 — 论文阅读与复盘

## 负责什么
论文检索 → 筛选 → 全文获取 → 日报 → 知识卡片 → 长期知识库 → 复盘笔记

## 放什么
- 每日论文日报
- 论文源文件 (PDF/metadata/note)
- 论文复盘笔记
- 长期知识库、待补读队列、候选论文
- 论文阅读 prompt 和模板
- 论文阅读、获取、解析相关脚本

## 不放什么
- 写作草稿和写作模板 → 03_写_论文写作
- 数据分析脚本 → 02_作图与分析
- PPT 材料 → 04_组会PPT
- 项目数据 → 06_数据资源库

## 知识图谱

论文阅读产出自动汇入知识图谱。本仓库附带 **1,127 节点 / 83,815 条关系** 的清洗后公开图谱：

```bash
python -m knowledge_graph query "RUSLE" --graph-file knowledge_graph/examples/public_graph.json
```

详见 [`knowledge_graph/examples/README.md`](../knowledge_graph/examples/README.md) 和根目录 [README](../README.md#knowledge-graph)。

## 核心脚本

`00_core_scripts/` 中的归档、补齐、检查和复盘脚本可随本工作流下载使用；其中 `enrich_archived_pdfs.py` 默认以自身所在的工作流根目录运行，不依赖某台电脑的盘符。每日定时筛选器仍由外部调度配置管理，下载者应按自己的系统配置任务，而不是复制他人的任务路径或账号配置。

归档 Markdown 仅写入源文件名与 SHA-256，不保留本机绝对路径。原始 PDF、提取文本与个人阅读记录仍属于研究资料，默认忽略，不应直接提交公开仓库。

## 与其他板块的边界
- 论文复盘 → 本板块 (03_论文复盘)
- 方法提取 → 07_方法与代码库
- 写作需求 → 03_写_论文写作
- 组会准备 → 04_组会PPT

## nature-skills 整合说明 (2026-06-09)

从 yuan1z0825/nature-skills 中提取了以下内容整合进 academic-workflow：

### 新增文件
- `../references/nature-skills/README.md` — 高质量期刊列表、论文 A/B/C/X 四级分级规则、nature-skills 整合说明
- `../prompts/paper_reading_gis_nature_prompt.md` — 论文阅读提示词（9 字段输出 + 方向匹配度 + 精读判断）
- `../prompts/paper_filter_luomingliang_direction_prompt.md` — 罗明良导师 7 方向论文筛选提示词（含定量打分公式）

### 如何使用
1. 日常读论文：复制 `prompts/paper_reading_gis_nature_prompt.md` 给 AI
2. 批量筛选论文：复制 `prompts/paper_filter_luomingliang_direction_prompt.md` 给 AI
3. 识别高质量期刊：查看 `references/nature-skills/README.md` 中的期刊列表
4. 需要 Nature 级别作图：运行 `npx skills add yuan1z0825/nature-skills@nature-figure`

### 不整合的内容
nature-figure/nature-polishing/nature-writing/nature-paper2ppt 的完整 static 文件树（100+ 文件）不放入项目目录。这些是独立 Claude Code skill，按需通过 `npx skills` 调用即可。详见 `references/nature-skills/README.md`。
