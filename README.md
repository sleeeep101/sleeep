# Academic Workflow

**A reproducible, AI-augmented research pipeline for geography, GIS, and remote sensing.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green)](https://python.org)

---

## What Is This?

Academic Workflow is a **full-stack scholarly production system** — from paper discovery to published manuscript, from raw spatial data to publication-ready figures. It provides battle-tested scaffolding for every stage of the geography research lifecycle, combining automation scripts, AI prompts, and reproducible project templates into one cohesive toolkit.

**Who it's for:** Graduate students and researchers in geography, GIS, remote sensing, or environmental science who want to move faster without sacrificing rigor.

**What it replaces:** Scattered scripts, ad-hoc AI prompting, hand-crafted project scaffolding, and the "where did I put that paper?" problem.

---

## What It Does

### 1. Paper Reading Pipeline (`01_读`)

The heart of the system. Ingests PDFs from any source, extracts text through a 7-engine cascade, scores papers on a unified 100-point rubric, and integrates findings into a living knowledge base.

| Step | Tool | Description |
|------|------|-------------|
| **Download** | `download_foreign_papers.py` | Automated retrieval from Semantic Scholar, arXiv, CrossRef |
| **Extract** | `pdf_ingest/` — 7-engine cascade | PyMuPDF → pdfplumber → pypdf → EasyOCR → Tesseract → MarkItDown → pymupdf4llm |
| **Score** | 7-dimension rubric (100 pts) | Novelty, method rigor, data quality, replicability, writing, relevance, evidence strength |
| **Card** | 22-field knowledge card | Structured extraction: method, dataset, innovation, limitations, transferable techniques |
| **Audit** | `cross_paper_audit.py` | Cross-paper consistency check — catches contradictions and unsupported claims |
| **Curate** | `daily_paper_curator.py` | Scheduled (12:00 daily) push-notification digest of the day's reading |

**Output:** Daily reading reports → 22-field knowledge cards → long-term knowledge base → weekly reading trends.

### 2. Scientific Figure Production (`02_作`)

GIS and data visualization toolchain with quality-tier governance:

- **QGIS Automation Module** — Script-driven layer management, styling, layout export at 300+ DPI
- **Origin Auto-Plot** — Automated OriginLab figure generation for SCI-tier charts
- **Figure Release Gate** — Pre-submission checklist: DPI check, colorblind-safe palette, font embedding, coordinate system annotation

**Output tiers:** T1 (publication, ≥300 DPI TIFF/EPS) → T2 (presentation, 150-200 DPI PNG) → T3 (internal draft, 72 DPI).

### 3. AI-Augmented Writing (`03_写`)

A 200+ GitHub-project-informed academic writing system, specialized for Chinese geography journals (GB/T 7714) and SCI journals:

- **9-step full paper generation** — Structured pipeline from outline → section drafts → integrated manuscript
- **Section-by-section workflow** — Targeted generation for Introduction, Methods, Results, Discussion
- **Anti-academic-fraud checklist** — Verifies every claim has an evidence source, every figure has raw data provenance
- **Writing technique extraction** — `05_writing_technique_extraction.md` mines published papers for reusable phrasing patterns

### 4. Research Topic Design (`05_选`)

- **Gap Detector** — `gap_detector.py` identifies research gaps by cross-referencing literature coverage against knowledge graph
- **Innovation Classification** — Framework for distinguishing method-gap, data-gap, region-gap, and scale-gap contributions
- **Advisor-Topic Fit Rules** — Systematic mapping between advisor expertise and candidate research directions

### 5. Group Meeting PPT (`04_组会`)

Automated slide generation with speaker scripts, evidence gates (every claim backed by a paper source), and meeting evidence quality scoring.

### 6. Reusable Methods Library (`07_方`)

Curated, indexed collection of GIS/remote sensing analysis methods extracted from the knowledge base — each method tagged by applicability domain, data requirements, and implementation complexity.

### 7. Knowledge Graph (`knowledge_graph/`)

Semantic query engine over the entire paper corpus:

```bash
python -m knowledge_graph query "RUSLE soil erosion Loess Plateau"
python -m knowledge_graph build   # rebuild from paper corpus
python -m knowledge_graph stats   # coverage statistics
```

---

## Project Architecture

```
academic-workflow/
├── 00_项目总览与导航/       Navigation hub, skill router, reference docs
├── 01_读_论文阅读与复盘/     ★ Paper reading: scripts, prompts, daily reports, knowledge base
├── 02_作图与分析/            Figures: QGIS automation, Origin plotting, visualization
├── 03_写_论文写作/            Writing: AI-assisted drafting, templates, checklists
├── 04_SCI三区论文项目/       Concrete paper projects (RUSLE, NE Sichuan)
├── 04_组会PPT/               Group meeting: slide generation, speaker notes
├── 05_选题与问题库/          Topic design: gap analysis, innovation classification
├── 07_方法与代码库/          Reusable methods: GIS/spatial analysis code library
├── knowledge_graph/          Semantic knowledge graph CLI
├── pdf_ingest/               7-engine PDF extraction module
├── scripts/                  Automation: daily curator, release builder, paper tracker
├── config/                   Unified path configuration
├── prompts/                  Reusable AI prompt encyclopedia
├── references/               Methodology references (Nature skills, GIS guardrails, etc.)
└── lib/                      Vendored frontend libraries (vis-network, tom-select)
```

**Design principles:**
- **Separation of concerns** — Control layer (Personal-Brain) vs. execution layer (academic-workflow) vs. project layer
- **Minimum modification** — Scripts read from `config/paths.json`; no hardcoded paths in shared code
- **Reproducible by default** — Every project starts from `_project_template/` with standardized directory structure
- **Privacy-aware** — `build_public_release.py` screens and redacts local paths before sharing

---

## Quick Start

```bash
# Clone
git clone https://github.com/sleeeep101/academic-skill.git
cd academic-skill

# Verify PDF extraction works
python -m unittest pdf_ingest.tests.test_end_to_end_public_fixture

# Test knowledge graph
python -m knowledge_graph query "soil erosion"

# Start a new reproducible project
cp -r "04_SCI三区论文项目/_project_template" projects/my-project

# Build a public release (safe sharing)
python scripts/build_public_release.py --destination ../public-copy --redact-local-paths
```

---

## Technology Highlights

### PDF Ingest: 7-Engine Cascade

Falls back gracefully: tries PyMuPDF first (fast, structured), descends through pdfplumber (table-aware), pypdf (pure Python), EasyOCR (scanned Chinese/English), Tesseract (legacy OCR), MarkItDown (LLM-powered), pymupdf4llm (Markdown-native). Each engine's output is scored for completeness; the best result wins.

### ScholarFlow: 8-Node Literature Review Pipeline

```bash
python 01_读_论文阅读与复盘/00_core_scripts/literature_review_pipeline.py "干热河谷植被恢复" --max 30
```

Automated: search → deduplicate → filter → download → extract → score → synthesize → export.

### Knowledge Graph

Entities extracted from paper cards: methods, datasets, study areas, temporal ranges, spatial scales. Query by keyword, browse by relation, identify coverage gaps.

### RUSLE Reference Implementation

A complete, documented RUSLE (Revised Universal Soil Loss Equation) implementation in Google Earth Engine, applied to purple-soil region of NE Sichuan. Serves as both a research project and a methodological template.

---

## Paper Card Example

> Real output from the 22-field knowledge card pipeline. Generated from auto-extracted full text; cards marked `PDF_TEXT_PARTIAL` require human review before entering the long-term knowledge base.

- **标题:** 地理信息系统中的数理统计方法应用分析
- **题名处理:** 中文题名已来自文件名或论文题名
- **作者:** 刘子辉
- **论文分类:** 遥感/GIS
- **阅读等级:** PDF_TEXT_PARTIAL
- **是否已读全文:** 否（仅基于自动提取正文，需人工复核）
- **正文有效长度:** 3,345 字符 / 1,447 词
- **识别章节:** 未稳定识别
- **一句话总结:** 围绕"地理信息系统中的数理统计方法应用分析"提供了可检查的研究线索；当前卡片基于本地全文自动抽取，适合先补齐日报，再决定是否进入正式精读或长期知识库。
- **研究问题:** 该文围绕《地理信息系统中的数理统计方法应用分析》展开，核心是把主题转化为可检索、可比较或可建模的问题。
- **数据来源:** 自动抽取未稳定识别数据来源；可从本地全文路径继续核对样本、区域、影像、统计资料或实验数据。
- **方法流程:** 在回归分析过程中，可借助逐步回归、向后回归等方法进行变量筛选与模型优化。
- **主要结果:** 自动抽取未稳定识别结果段落；本卡片先保留全文路径、研究问题、数据和方法线索，避免低分或结构异常论文完全缺卡。
- **局限与复核点:** 未在自动抽取文本中稳定识别局限性段落；若进入正式精读，应复核实验边界、数据适用范围和结论外推条件。
- **可迁移到 GIS / 遥感 / DEM / 空间分析的点:** 可迁移到 GIS 空间叠加、缓冲区、网络可达性、热点识别或空间插值任务。
- **可转 AI Code / 学习任务:** 把论文中的数据、方法、结果字段整理成一张可检索的 Obsidian 表格；若方法可复现，拆成一个最小 GIS/遥感/统计分析 notebook：数据读取、预处理、指标计算、结果图；把图表表达和结论句式加入中文学术表达积累库，保留来源日报日期。
- **处理建议:** 先保留在日报补充卡片中；若要入长期知识库，再按全文证据、重复情况和个人研究方向进行二次筛选。
- **不确定项:** 样本、参数、统计检验和结果仅在自动提取中可见时才记录；未稳定识别的内容均待全文复核。
- **分数处理:** 本次按用户要求补齐卡片，不以评分高低作为是否生成卡片的门槛。

> **Note:** This card was generated from auto-extracted text and has NOT passed the `PDF_TEXT_FULL` quality gate. Paths above are illustrative; actual local file paths are not bundled in this repository. See [`01_读_论文阅读与复盘/05_阅读提示词/02_knowledge_card_generation.md`](01_读_论文阅读与复盘/05_阅读提示词/02_knowledge_card_generation.md) for the 22-field card schema.

---

## Knowledge Graph

The repository ships a **pre-built knowledge graph** with 1,127 paper nodes and 83,815 semantic relations, extracted from a geography/GIS/remote-sensing reading corpus. All personal paths have been redacted.

```bash
# Query the bundled graph
python -m knowledge_graph query "RUSLE soil erosion" --graph-file knowledge_graph/examples/public_graph.json

# Statistics
python -m knowledge_graph stats --graph-file knowledge_graph/examples/public_graph.json

# Build your own from local papers
python -m knowledge_graph build
```

See [`knowledge_graph/examples/README.md`](knowledge_graph/examples/README.md) for details on the bundled dataset, privacy policy, and how to build a personal graph from your own reading corpus.

---

## License

MIT. See [LICENSE](LICENSE).

## Attribution

The reproducible-project structure is informed by [The Turing Way](https://github.com/the-turing-way/reproducible-project-template) and [mahesh-panchal/academic-project-template](https://github.com/mahesh-panchal/academic-project-template). All content is original.
