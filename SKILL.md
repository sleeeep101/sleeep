# Academic Workflow — 科研论文阅读与知识积累

> 唯一入口。本文件只做路由（≤150行）。详细规则 → `references/` 目录按需加载。

## 系统位置

| 资源 | 路径 |
|------|------|
| 定时任务 | `scripts/daily_paper_curator.py` → Task `DailyPaperCurator_1200` |
| PDF提取 | `pdf_ingest/`（7引擎级联）→ CLI `scripts/ingest_pdf.py` |
| 外文下载 | `01_读_论文阅读与复盘/00_core_scripts/download_foreign_papers.py` |
| 每日产出 | `01_读_论文阅读与复盘/01_每日论文/YYYY-MM-DD_论文阅读日报.md` |
| 长期知识库 | `01_读_论文阅读与复盘/04_长期知识库/长期知识库.md` |
| **知识图谱** | `knowledge_graph/` — CLI: `python -m knowledge_graph build\|query\|stats` |
| 配置入口 | `config/paths.json` |
| 脚本清单 | [`scripts/README.md`](scripts/README.md) |

## 工作流路由

| 任务 | 触发 | 详细规则 |
|------|------|---------|
| 每日论文批量精读 | 桌面有PDF → `process_desktop_pdfs` | `references/daily-paper-reading.md` |
| 论文评分/入库 | 读完每篇 → 7维100分制 | `references/paper-grading.md` |
| 知识卡片生成 | 入库时 → 22字段 | `references/knowledge-card.md` |
| 写作/润色/投稿 | 学术写作任务 | `references/academic-writing.md` |
| 实验设计 | 研究设计任务 | `references/experiment-design.md` |
| GIS数据处理 | 空间数据任务 | `references/gis-data-processing.md` |
| 外文论文检索下载 | 下载论文 | `references/foreign-paper-download.md` |
| 组会PPT | 组会准备 | `references/group-meeting.md` |
| 投稿/审稿 | 论文投稿 | `references/submission-review.md` |
| 知识管理 | KG/记忆 | `references/knowledge-management.md` |

## 快速入口

```bash
# 知识图谱
python -m knowledge_graph query "<关键词>"

# 外文下载
python 01_读_论文阅读与复盘/00_core_scripts/download_foreign_papers.py --preset ALL --max-download 20

# PDF提取
python scripts/ingest_pdf.py --pdf "path/to/paper.pdf"

# 文献综述（ScholarFlow 8节点流水线）
python 01_读_论文阅读与复盘/00_core_scripts/literature_review_pipeline.py "研究主题" --max 30

# 论文评分（关键词+ARS混合）
# 自动: PDF_TEXT_FULL → ARS 5维 + 关键词8维混合 | ABSTRACT_ONLY → 关键词8维初筛
```

## 写作方法论（跨仓库精进）

论文写作任务自动加载 `references/nature-skills/cross-repo-insights.md`，包含四仓库精进提取：

| 方法论 | 触发场景 | 详见 |
|--------|---------|------|
| 声明-证据映射 | 写作/修订/投稿前 | §一 |
| 五层审计优先级 | 修改手稿（方向→逻辑→视觉→术语→语言） | §二 |
| Introduction-Twice | 新论文启动 | §三 |
| 图表声明规划 | 设计/审计论文图表 | §五 |
| 七种压缩操作 | 终稿压缩 | §六 |
| 逆向大纲 + 主题句先行 | 修订现有章节 | §七 |
| 英文散文风格规则 | 英文段落润色 | §八 |
| Results 段落架构 8 项 | Results 小节修订 | §九 |
| LaTeX 编译诊断 + GB/T 7714 | 中文核心投稿收尾 | §十一 |

## 整合工具

| 工具 | 类型 | 用途 | 使用方式 |
|------|------|------|---------|
| `academic-research-skills` | Plugin | 5维论文评分+7人审稿团 | 全文论文自动调用，与关键词8维混合评分 |
| `literature_review_pipeline.py` | 核心脚本 | ScholarFlow 8节点文献综述 | `python literature_review_pipeline.py "主题"` |
| `RUSLE/` | 参考实现 | GEE RUSLE侵蚀模型 | 位于 `07_方法与代码库/RUSLE/` |

## 核心质量标准

| 指标 | 基线 | 详见 |
|------|------|------|
| 每日最少精读 | 3篇（≥60分入库） | `references/daily-paper-reading.md` |
| 入库阈值 | ≥60/100 | `references/paper-grading.md` |
| 知识卡片深度 | 22字段 + 3分析方法 | `references/knowledge-card.md` |
| 论文评分 | 统一7维100分制（原7维+ARS 5维合并） | `references/paper-grading.md` |

## 板块索引

| 编号 | 板块 | 用途 |
|------|------|------|
| 00 | 项目总览与导航 | 入口/配置/参考 |
| 01 | 读_论文阅读与复盘 | 论文获取→精读→日报→长期知识库 |
| 02 | 作图与分析 | QGIS自动化/Origin绑图/数据可视化 |
| 03 | 写_论文写作 | 模板/投稿/审稿/AI写作 |
| 04 | SCI三区论文项目 | 具体论文项目(RUSLE川东北) |
| 05 | 选题与问题库 | 空白识别/创新分类/研究规划 |
| 07 | 方法与代码库 | 可复用分析代码 |
| 90 | 待人工确认 | 需人工审核的内容 |
| 98 | 迁移记录 | 历史迁移日志 |

## 关联

- 开发纪律 → `dev-discipline` skill
- 学术写作+审稿评分 → `academic-paper-writing` skill + `academic-research-skills` plugin（7人审稿团+5维评分）
- 论文配图 → `scientific-figure` skill
- 组会PPT → `group-meeting-ppt` skill
- PDF提取 → `pdf-image-text-extractor` skill
- DEM/地形分析 → `dem-terrain-mcp` MCP server（已注册）

## 其他工具

| 工具 | 类型 | 用途 |
|------|------|------|
| `dem-terrain-mcp` | MCP Server | DEM超分辨率+侵蚀风险评分（已注册） |
| `iMPACT-erosion` | 教育工具 | 侵蚀建模Jupyter教学（浏览器运行） |
| `ScholarFlow` | 参考设计 | 8节点文献综述流水线 |

- 跨工具交接 → `<LOCAL_PATH>`
