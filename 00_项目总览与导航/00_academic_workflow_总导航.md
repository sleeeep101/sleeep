# 00 academic-workflow 总导航

> 最后更新: 2026-07-13
> academic-workflow = 学术执行层。10板块 + 读/作/写/讲 4核心功能。
> 质量基线: 2026-07-13 日报（1,566行/62卡片/100%覆盖/KB入库62篇/评分≥60全部入库）

---

## 1. 当前目录结构 (3层)

```
academic-workflow/
├── 00_项目总览与导航/          ← 总导航、SKILL.md、references/、个人学术信息、毕业要求、历史报告
├── 01_读_论文阅读与复盘/       ← ★ 当前最核心板块
│   ├── 00_core_scripts/         ← 桌面PDF处理（process_desktop_pdfs + backfill + _shared_constants）
│   ├── 01_每日论文/             ← 每日日报
│   ├── 02_论文阅读库/           ← paper_sources/ + fulltext_papers/（按日期分文件夹）+ 已读论文清单
│   ├── 03_论文复盘/             ← 论文复盘笔记
│   ├── 04_长期知识库/           ← 长期知识库.md + 可能的创新点.md
│   └── 05_阅读提示词/           ← 阅读+卡片+处理流水线 prompt（4个文件）
├── 02_作图与分析/
│   ├── 00_core_scripts/         ← 作图 prompt
│   ├── 01_作图/                 ← origin_auto_plot 工具
│   ├── 02_分析/                 ← 数据分析脚本
│   └── 03_图表模板/
├── 03_写_论文写作/              ← 写子系统 (原 write/，30+文件)
│   ├── 00_core_scripts/         ← 写作脚本
│   ├── 01_论文草稿/
│   ├── 02_写作模板/
│   └── 03_段落素材/
├── 04_组会PPT/                  ← 组会子系统 (原 组会/，25+文件)
│   ├── 00_core_scripts/         ← PPT 脚本
│   ├── 01_组会材料/
│   ├── 02_PPT文件/
│   └── 03_PPT模板/
├── 05_选题与问题库/             ← 毕业要求_学位论文与发表论文.md
├── 06_数据资源库/               ← 空 (跟随项目)
├── 07_方法与代码库/             ← 方法库索引.md
├── 08_实验与结果库/             ← 空 (跟随项目)
├── 09_导师沟通与任务管理/       ← 空 (归 Personal-Brain)
├── 10_项目复盘与作品集/         ← 空 (归 Personal-Brain)
├── pdf_ingest/                  ← PDF提取模块（7引擎级联），被所有提取任务调用
├── scripts/                     ← 定时任务核心（daily_paper_curator.py）+ 工具脚本（8个精简后文件）
├── logs/                        ← paper_tracker.db + 运行日志
├── agents/                      ← Agent 配置
├── 90_待人工确认/
├── 98_迁移记录/
└── 99_归档备份/
```

---

## 2. 10 板块说明

10 板块是**项目文件组织框架**，不是论文 category 分类。

| # | 板块 | 状态 | 核心目录 |
|---|------|------|---------|
| 1 | 选题与问题库 | **已有** | `05_选题与问题库/` → 毕业要求已入库 |
| 2 | 论文阅读库 | **活跃** | `01_读_论文阅读与复盘/` |
| 3 | 数据资源库 | 暂缓 | `06_数据资源库/` |
| 4 | 方法与代码库 | 部分 | `07_方法与代码库/` |
| 5 | 作图与可视化库 | 部分 | `02_作图与分析/` |
| 6 | 实验与结果库 | 暂缓 | `08_实验与结果库/` |
| 7 | 论文写作库 | **已有** | `03_写_论文写作/` |
| 8 | 组会PPT库 | **已有** | `04_组会PPT/` |
| 9 | 导师沟通与任务管理 | 归PB | `09_导师沟通与任务管理/` |
| 10 | 项目复盘与作品集 | 归PB | `10_项目复盘与作品集/` |

**项目板块用于放文件。论文分类用于标记论文研究方向。两者不能混用。**

---

## 3. 论文分类 5 类白名单

论文 category 使用独立体系，不跟随板块名称：

| # | 论文分类 | 说明 |
|---|---------|------|
| 1 | 遥感/GIS | 遥感图像、GIS 空间分析、地理信息 |
| 2 | AI/计算机 | 机器学习、深度学习、计算机视觉 |
| 3 | 统计/方法 | 统计方法、因果推断、计量 |
| 4 | 生态环境 | 生态、水文、气候、土壤、植被 |
| 5 | 交叉学科 | 无法归入以上4类的论文（默认） |

**Tags 标准格式:** `关键词1 关键词2 关键词3 | 论文分类 | 来源: arXiv/Semantic Scholar`

---

## 4. 核心脚本位置

| 脚本 | 路径 | 状态 |
|------|------|------|
| daily_paper_curator.py | `scripts/daily_paper_curator.py` | 定时任务核心 |
| process_desktop_pdfs | `01_读/00_core_scripts/process_desktop_pdfs_20260623.py` | 桌面PDF全量处理 |
| backfill_daily_paper_cards | `01_读/00_core_scripts/backfill_daily_paper_cards.py` | 日报卡片补齐 |
| _shared_constants | `01_读/00_core_scripts/_shared_constants.py` | 共享常量（BANNED/METHOD/评分/工具函数） |
| pdf_ingest | `pdf_ingest/` | 7引擎PDF提取（pymupdf4llm→…→markitdown） |
| ingest_pdf CLI | `scripts/ingest_pdf.py` | pdf_ingest 命令行入口 |
| fulltext_utils.py | `scripts/fulltext_utils.py` | PDF/HTML全文提取+解析（fallback） |
| paper_source_utils.py | `scripts/paper_source_utils.py` | 论文源文件工具 |
| run_paper_curator.bat | `scripts/run_paper_curator.bat` | 定时任务入口 |
| paper_tracker.db | `logs/paper_tracker.db` | 论文追踪数据库 |
| **knowledge_graph** | `knowledge_graph/` | **公开图谱 1,127节点/83,815边** (`examples/public_graph.json`) |

> `scripts/` 目录 7月13日已清理：删除9个冗余脚本（备份/临时/零引用），保留8个活跃文件。

---

## 5. 旧目录迁移说明

| 原路径 | 新路径 |
|--------|--------|
| `长期知识库.md` | `01_读_论文阅读与复盘/04_长期知识库/长期知识库.md` |
| `待补读队列.md` | `01_读_论文阅读与复盘/04_长期知识库/待补读队列.md` |
| `candidate_papers/` | `01_读_论文阅读与复盘/04_长期知识库/abstract_only_queue.md` |
| `reports/daily/` | `01_读_论文阅读与复盘/01_每日论文/` |
| `references/` | `00_项目总览与导航/references/` |
| `prompts/` (阅读) | `01_读_论文阅读与复盘/05_阅读提示词/` |
| `tools/origin_auto_plot/` | `02_作图与分析/01_作图/origin_auto_plot/` |
| `write/` | `03_写_论文写作/` |
| `组会/` | `04_组会PPT/` |
| `paper_sources/` | `01_读_论文阅读与复盘/02_论文阅读库/paper_sources/` |

---

## 6. 待人工确认事项

1. `scripts/` 是否后续迁移到 `01_读/00_core_scripts/`（等定时任务稳定后）
2. `长期知识库.md` 中 Marzouk 2024 条目的 Tags 格式（当前为自由文本，不符合标准格式）

---

## 7. 清理记录

| 日期 | 操作 | 数量 | 详情 |
|------|------|------|------|
| 2026-07-13 | 删除冗余脚本 | 9个 | scripts/ 清理：备份/临时/零引用脚本 |
| 2026-07-13 | 整合共享常量 | 1个新建 | _shared_constants.py 合并两个脚本的重复常量 |
| 2026-07-13 | 脚本集成 pdf_ingest | 2个修改 | process_desktop_pdfs + backfill 改用 pdf_ingest 为第一引擎 |
| 2026-07-13 | 修复硬编码路径 | 3处 | run_paper_curator.bat / process_desktop_pdfs / workflow prompt |
| 2026-07-13 | 统一评分体系 | 全量 | 旧加分制废弃，统一为7维100分制 |
| 2026-07-13 | SKILL.md 重建 | 1个 | 新增桌面PDF工作流/KB入库规则/质量基线/工具链章节 |
| 2026-06-06 | 删除 __pycache__ | 4目录/22 .pyc | Python缓存，自动重建 |
| 2026-06-06 | 删除空孤儿目录 | 7个 | 迁移后遗留的空子目录 |
| 2026-06-06 | 删除重复文件 | 1个 | group_meeting_test_report |
| 2026-06-06 | 板块分类整理 | 全部文件 | 见 98_迁移记录/ |

---

## 8. 备份位置

| 备份名 | 路径 | 用途 |
|--------|------|------|
| 板块整理前 | `99_归档备份/before_restructure_20260606_0920/` | 板块重组前备份 |
| 完全分类清理前 | `99_归档备份/before_full_classify_cleanup_20260606_0956/` | 本次清理前备份 |
| 版本归档 | `99_归档备份/version_archive_20260606_0956/` | 旧 backup 脚本归档 |
| 上次清理备份 | `99_归档备份/backup_before_cleaning_20260604_212427/` | 2026-06-04 清理备份 |
