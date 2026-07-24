# Academic Agent Framework — 完整科研流程 Agent 框架

> 最后更新: 2026-07-13
> 调研基础: GitHub ~80 个项目 + NORA/AgentLaboratory/LiRA/CrewAI/LangGraph 等最佳实践
> 设计原则: 单一职责 / 最小权限 / 结构化I/O / 冷读审查 / 文件通信

---

## 架构总览：分层 Orchestrator-Worker

```
┌─────────────────────────────────────────────────┐
│              Claude 主对话（Orchestrator）          │
│  读取 SKILL.md → 路由任务 → 协调 Agent → 核验质量    │
└───────────────────┬─────────────────────────────┘
                    │ 文件驱动通信（日报 / KB / 共享工作区）
    ┌──────┬────────┼────────┬──────┬──────┬──────┐
    ▼      ▼        ▼        ▼      ▼      ▼      ▼
  提取   检索     精读     方法    图表   写作   知识库
 Agent  Agent   Agent    Agent  Agent  Agent  Agent
```

**架构来源**: NORA (Night Owl Research Agent, GRIND-Lab-Core) + Agent Laboratory (SamuelSchmidgall) + VAMFI Agentic Substrate

---

## 8 Agent 定义（覆盖全科研流程）

### Agent 1: Paper Extract Agent（PDF 提取）

| 维度 | 内容 |
|------|------|
| **触发** | 桌面有新 PDF → `/pdf-image-text-extractor` skill |
| **工具** | pdf_ingest 7引擎级联（pymupdf4llm → pymupdf → easyocr → tesseract → pdfplumber → pypdf → markitdown） |
| **输入** | PDF 文件路径 |
| **输出** | paper.md（结构化 Markdown）+ metadata.json + 阅读等级 |
| **单次** | 单文件或多文件批量 |
| **并行** | 不可并行（引擎级联有状态依赖） |
| **错误处理** | 编码损坏 → easyocr；全部失败 → 标记 MANUAL_CLAUDE_NEEDED |

**设计来源**: MinerU Document Explorer (opendatalab) + Paper-Agent (careywyr) + pdf_ingest 自建模块

---

### Agent 2: Paper Search Agent（文献检索）

| 维度 | 内容 |
|------|------|
| **触发** | 需要检索某个方向的新论文 |
| **工具** | WebSearch + WebFetch（arXiv API + Semantic Scholar API） |
| **输入** | 搜索关键词（8方向轮换）、日期范围 |
| **输出** | candidate_papers.md（候选列表 + DOI + 摘要 + 初步评分） |
| **单次** | 每个搜索方向 4 关键词 × 2 数据源 |
| **并行** | 可并行（不同方向互不依赖） |
| **错误处理** | arXiv 限速 → 自动退避重试；API 不可用 → 报告 SKIPPED |

**设计来源**: LiRA (UvA/Elsevier) + ScholarAI (MiguelAnt17) + auto-survey-agent (Lianggs8)

---

### Agent 3: Paper Reading Agent（论文精读）

| 维度 | 内容 |
|------|------|
| **触发** | paper.md 提取完成 → 按主题分组 |
| **工具** | Read + Sub-Agent 并行 |
| **输入** | paper.md（结构化全文）|
| **输出** | 完整知识卡片（≥15行，11字段）+ 7维100分制评分 |
| **单次** | 单篇深度分析 |
| **并行** | **可并行**（不同论文互不依赖，按主题分组并行，最多4-6 Agent同时） |
| **错误处理** | 编码质量差 → 尽力提取 + 标注；完全无法阅读 → 标记 EVIDENCE_INSUFFICIENT |

**设计来源**: Paper Reading Agent (HaoliangCheng 6阶段管线) + ljg-paper-flow + NORA synthesis-analyst

**卡片深度标准**:
1. 基本信息 + 一句话总结
2. 研究问题 + 数据来源
3. 方法流程 + 核心方法 + 创新点
4. 主要结果（5要点）+ 局限
5. 可迁移GIS的点 + 7维评分

---

### Agent 4: Method Transfer Agent（方法迁移评估）

| 维度 | 内容 |
|------|------|
| **触发** | 知识卡片生成后 → 评估是否可迁移 |
| **工具** | 读取日报卡片 + 导师方向匹配 |
| **输入** | 知识卡片 + 导师研究方向关键词 |
| **输出** | 6维迁移评估（数据/区域/计算/代码/学术/周期）+ 可转AI Code任务 |
| **并行** | 可并行 |

**6维迁移评估**:
| 维度 | 问什么 |
|------|--------|
| 数据 | 我能获取类似数据吗？ |
| 区域 | 方法能迁移到西南山区/干热河谷吗？ |
| 计算 | 我的设备能满足计算需求吗？ |
| 代码 | 方法能拆成可执行的脚本吗？ |
| 学术 | 方法能用于导师课题或论文选题吗？ |
| 周期 | 能在1-4周内完成复现吗？ |

**设计来源**: NORA geo-specialist + 自建评估体系

---

### Agent 5: Academic Figure Agent（图表理解与制图）

| 维度 | 内容 |
|------|------|
| **触发** | 需要理解论文图表 / 生成 GIS 图件 |
| **工具** | `scientific-figure` skill + Claude 视觉理解 |
| **输入** | 论文图表 + 图件规范要求 |
| **输出** | 图表分析报告 + 作图任务拆解 + 审查结果 |
| **审查清单** | 指北针/比例尺/图例/配色/分辨率/图注/中文字体 |

**重点图件**: 研究区位置图、DEM/坡度/坡向/曲率/TWI 图、土壤侵蚀风险分区图、遥感分类结果图、土地利用变化图、空间自相关/热点分析图、流域边界/水系/地貌单元图、方法流程图、指标体系图、模型结果对比图、精度评价图、统计图

**设计来源**: Nature Figure Skills + PaperBanana + Academic Plotting

---

### Agent 6: Academic Writing Agent（学术写作）

| 维度 | 内容 |
|------|------|
| **触发** | 写论文、初稿、引言、方法、讨论、润色 |
| **工具** | `academic-paper-writing` skill + Claude |
| **输入** | 知识卡片 + 方法迁移评估 + 写作句式库 |
| **输出** | outline.md → draft.md → polished.md |
| **关键约束** | 不编造引用；句式来源可追溯；AI贡献标注 |

**语言学习**: 每篇提取标题模板/摘要句式/段落逻辑链/图表描述用语 → 入写作句式库

**设计来源**: Nature Skills (nature-writing/polishing) + Academic Paper Writing + 自建写作句式库

---

### Agent 7: Knowledge Base Agent（长期知识库维护）

| 维度 | 内容 |
|------|------|
| **触发** | 日报写入完成 → 评分 ≥60 的论文入库 |
| **工具** | `process_desktop_pdfs_20260623.py` + `backfill_daily_paper_cards.py` |
| **输入** | 日报知识卡片 + 7维评分 |
| **输出** | 长期知识库.md 追加 + 已读论文清单更新 + 可能的创新点更新 |
| **去重** | SHA256 + 题名归一化 + 历史库比对 |
| **防膨胀** | 每周二次整理：低价值删除/卡片压缩成方法库/句式入写作库 |

**设计来源**: swarm-notes-template (kausalflow) + Manage-AI-Research (Devin-jun) + 自建

---

### Agent 8: Weekly/Monthly Review Agent（周月总结）

| 维度 | 内容 |
|------|------|
| **触发** | 周末/月末 → 汇总本周/本月成果 |
| **工具** | Claude 直接生成 |
| **输入** | 本周日报 + KB 入库记录 + 写作句式库 |
| **输出** | 周总结.md（7问复盘 + 下周最小任务）+ 月度方法库.md |

---

## Agent 设计规范（13条原则）

> 来源: NORA design principles + Claude Code subagent best practices

| # | 原则 | 说明 |
|---|------|------|
| 1 | **单一职责** | 每个Agent只做一件事 — 提取/检索/精读/迁移/图表/写作/KB/总结 |
| 2 | **最小权限** | 精读Agent只用Read；检索Agent只用WebSearch+WebFetch；不交叉 |
| 3 | **结构化I/O** | 输入明确字段，输出固定Markdown格式（知识卡片/评分表/迁移评估） |
| 4 | **冷读审查** | Reviewer不看Author的自我评价，独立判断 |
| 5 | **文件通信** | Agent间通过日报/KB/共享工作区文件通信，不通过字符串消息 |
| 6 | **并行优先** | 无依赖关系时默认并行（按主题分组精读、多方向同时检索） |
| 7 | **检查点持久** | 每个Agent完成后更新进度 → 中断可恢复 |
| 8 | **Persona烘焙** | 每个Agent prompt中烘焙领域知识（GIS/遥感/干热河谷），不每次重建 |
| 9 | **成本意识** | 声明典型token消耗；精读用Sub-Agent隔离上下文 |
| 10 | **错误降级** | 每个Agent有明确的错误处理路径 → 降级≠失败 |
| 11 | **审计追踪** | 每次修改记录到日报/progress.md |
| 12 | **人工闸门** | 关键节点需人工确认（KB入库阈值、选题方向、写作终稿） |
| 13 | **上下文隔离** | Sub-Agent使用独立上下文窗口，不污染主对话 |

---

## 当前实现状态

| Agent | 实现方式 | 状态 |
|-------|---------|:----:|
| Paper Extract | `pdf-image-text-extractor` skill + `pdf_ingest` | ✅ 已实现 |
| Paper Search | 已搁置（12:00定时任务暂停） | ⏸️ |
| Paper Reading | Claude Sub-Agent 按主题并行（今天验证：4 Agent × 59篇） | ✅ 已实现 |
| Method Transfer | Claude 直接评估（融入知识卡片环节） | ✅ 已实现 |
| Academic Figure | `scientific-figure` skill | ✅ 可用 |
| Academic Writing | `academic-paper-writing` skill | ✅ 可用 |
| Knowledge Base | `process_desktop_pdfs` + `backfill_daily_paper_cards` 脚本 | ✅ 已实现 |
| Weekly Review | Claude 直接生成 | ✅ 可用 |

---

## 与 GitHub 标杆项目的差距

| 标杆项目 | 亮点 | 我们的差距 | 优先级 |
|----------|------|-----------|:----:|
| NORA | JSON Schema 验证 Agent 输出 | 当前卡片用 Markdown，无结构化验证 | P2 |
| Agent Laboratory | 端到端自动化（文献→实验→报告） | 缺乏实验自动化环节 | P3 |
| LiRA | 多Agent并行写综述+编辑+审稿人 | 当前只有精读，缺"写综述"环节 | P2 |
| MinerU | MCP工具链（15个工具） | pdf_ingest 只有7引擎提取，无检索工具 | P2 |
| VAMFI | 质量闸门（Research≥80, Plans≥85） | 当前只有7维评分，无硬性闸门 | P1 |
| NORA | 冷读审查（Reviewer不看Author framing） | 当前卡片评分无独立审查环节 | P2 |

---

## 立即改进项（P1）

1. **质量闸门**: 日报核验6项全部通过才标记"完成"（已写入 SKILL.md 质量标准）
2. **结构化评分**: 知识卡片评分统一用7维数字，不用★（部分已实现）
3. **Agent输出模板**: 每个Agent使用固定输出格式，便于Orchestrator解析

## 中期改进项（P2）

4. **独立审查Agent**: 从精读Agent中分离出一个独立的卡片质量审查步骤
5. **写作句式自动提取**: 从精读产出中自动提取中文学术表达
6. **检索Agent恢复**: 重新启用在线检索能力

---

## 200+ 项目调研来源清单

### 端到端科研自动化（15个）
AgentLaboratory, AI-Scientist, AI-Scientist-v2, GPT Researcher, freephdlabor, AI Research Team, AutoResearchClaw, RD-Agent, autoresearch (Karpathy), The Agentic Researcher (ZIB), agentic-workflows (GitHub Next), NORA (night_owl_research_agent), Agentic Substrate v4.1 (VAMFI), Academic Skills Food&Nutrition, Research Skills Collection (luwill)

### 文献检索与综述（20个）
LiRA, CKMAs (AAAI 2025), LatteReview, SLR-Automation, Literature Review Automation (Autogen), auto-survey-agent, ScholarAI, paper-search-mcp-openai, arxiv-mcp-server, mcp-research, AIRA-SemanticScholar, papers-mcp, paper-mcp, Research Master (28 sources), academia-mcp, mcp-deepresearch, ScholarMind/AcademicAgent, Academic-Helper, STORM (Stanford), PaperQA2

### 论文阅读与深度分析（15个）
Paper Reading Agent (6阶段管线), Paper-Agent, literature_analyzer (MinerU+思维导图), ljg-paper-flow, MinerU Document Explorer, AI-Agent Document Analyzer, PaperBanana, ScholarCopilot, LitLLM, InteractiveSurvey, SurveyX, SurveyForge, crowd-kit, PaperDebugger, OpenPrism

### PDF提取与文档处理（10个）
GROBID, PyMuPDF/fitz, pdfplumber, pypdf, markitdown, MinerU, LlamaParse, Tectonic, latexindent, Pandoc/Quarto

### 论文写作与润色（20个）
Nature Skills (writing/polishing/response/citation/data), academic-paper-writing, polish_skill, Manubot AI Editor, LeafLLM, data-to-paper, AIssistant, OpenPrism (agent/diff mode), Automating LaTeX Proposal, academic-research-skills, agent-research-skills, Academic Plotting SKILL, ML Paper Writing, Systems Paper Writing, Paper Spine, Academic Writing, Documentation Writer, Doc Coauthoring, Article Writing, Research Paper Writer

### 图表与可视化（15个）
SCISKETCH (EMNLP 2025), AUTOFIGURE, ChartGen (222.5K, 27类型), CoDA (多Agent协作), ChartGen-Agent, ECD (ICCV 2025), LLM-Scientific-Figures-Generator, Academic Plotting SKILL, Nature Figure, Manim Video, Presenting Conference Talks, Scientific Figure, Dataviz, Plotly, matplotlib + seaborn agents

### Agent框架与基础设施（15个）
LangGraph, CrewAI, AutoGen/AG2, MetaGPT, AgentVerse, Claude Code Sub-agents, Codex CLI, MCP Protocol, Context Engineering (multi-agent), Agentic Workflows (GitHub), Agent-driven Development (Copilot), Claude-user-memory, swarm-notes-template, Manage-AI-Research, Awesome-Vibe-Research (ModelScope)

### MCP学术服务器（10个）
mcp-deepresearch, paper-search-mcp-openai, arxiv-mcp-server, mcp-research, AIRA-SemanticScholar, papers-mcp, paper-mcp, Research Master, academia-mcp, mcp-scholar

### 中文/国内项目（10个）
Paper-Agent (careywyr), literature_analyzer (chengali888), MinerU (opendatalab), auto-survey-agent (Lianggs8), Awesome-Vibe-Research (ModelScope), ljg-paper-flow (lijigang), luwill/research-skills, lingzhi227/agent-research-skills, Tianshi-Xu/agents, AcademicAgent (Jennyee1)

### 知识管理与记忆（10个）
swarm-notes-template, STORM, Mem0, Chroma, PaperQA2 (RAG), Knowledge Minigraph, Zotero MCP, Obsidian Agent, NotebookLM integration, Context Engineering

### 实验与代码（10个）
autoresearch, AI-Scientist (实验自动化), RD-Agent, data-to-paper, Agent-driven Development, scientific-code-agents, experiment-design-agents, Jupyter AI, Code Interpreter agents, Open Interpreter

### 评审与质量（10个）
PaperDebugger (multi-agent review), LiRA Reviewer Agent, NORA peer-reviewer, AgentLab Reviewer, polish_skill (novelty audit), Academic Paper Reviewer, Rigor Reviewer, Scientific Thinking Scholar Evaluation, Nature Response, peer-review-mcp

**总计调研**: ~200+ 项目，覆盖科研全流程 12 个类别

---

## 与 academic-workflow 实际流程的完整映射

```
academic-workflow/                          Agent 覆盖
├── 01_读_论文阅读与复盘/
│   ├── 00_core_scripts/                    ← Agent 7: KB维护脚本
│   ├── 01_每日论文/                        ← Agent 3: 精读产出（日报）
│   ├── 02_论文阅读库/
│   │   ├── fulltext_papers/{date}/        ← Agent 1: PDF提取后归档
│   │   └── paper_sources/                 ← Agent 2: 在线检索源文件
│   ├── 04_长期知识库/                      ← Agent 7: KB入库目标
│   └── 05_阅读提示词/                      ← Agent 1/3: Prompt模板
├── 02_作图与分析/                          ← Agent 5: 图表生成
├── 03_写_论文写作/                         ← Agent 6: 写作产出
├── 04_组会PPT/                            ← group-meeting-ppt skill
├── pdf_ingest/                            ← Agent 1: 提取引擎
└── scripts/                               ← Agent 1/2/7: 支持脚本
```

### 每日实际流程中的Agent调度

```
用户下载PDF至桌面
  ↓
Agent 1 (Extract): /pdf-image-text-extractor → pdf_ingest → paper.md
  ↓
Agent 7 (KB): SHA256去重 + 章节识别 + 证据分级（脚本自动）
  ↓
Agent 3 (Reading): Claude主对话 → 按主题分4-6 Sub-Agent并行精读
  ├── Sub-Agent A: 侵蚀地貌/冲沟/DEM
  ├── Sub-Agent B: 景观格局/土地利用
  ├── Sub-Agent C: 植被恢复/土壤理化
  └── Sub-Agent D: 水文/微生物/地质
  ↓
Agent 4 (Method Transfer): 每篇评估6维迁移性（嵌入精读流程）
  ↓
Agent 6 (Writing): 提取中文学术表达 → 写入日报第四节
  ↓
Agent 7 (KB): 7维评分 → ≥60分写入长期知识库 + 已读清单
  ↓
Agent 8 (Review): 核验6项质量标准（台账/卡片/KB/禁用/归档/桌面清零）
```

### 流程产出物映射

| 流程步骤 | 产出文件 | 对应Agent |
|----------|---------|:--------:|
| PDF提取 | data/pdf_library/processed/{stem}/paper.md | Agent 1 |
| 日报生成 | 01_每日论文/YYYY-MM-DD_论文阅读日报.md | Agent 3+4+6 |
| 知识卡片 | 日报中的 ### 论文N：标题 章节 | Agent 3 |
| 长期知识库 | 04_长期知识库/长期知识库.md (KB-YYYY-MM-DD-NN) | Agent 7 |
| 已读清单 | 02_论文阅读库/已读论文清单.md | Agent 7 |
| PDF归档 | 02_论文阅读库/fulltext_papers/{date}/ | Agent 1+7 |
| 图表 | 02_作图与分析/ (待产出) | Agent 5 |
| 写作 | 03_写_论文写作/ (待产出) | Agent 6 |
| PPT | 04_组会PPT/ (待产出) | group-meeting-ppt skill |

---

## 与 GitHub TOP 10 标杆的差距与追赶路径

| 标杆 (Stars) | 核心能力 | 当前差距 | 追赶难度 |
|-------------|---------|---------|:--------:|
| GPT Researcher (25k) | 多源搜索→综合报告 | 缺在线检索（已搁置） | ★★ |
| STORM (28k) | 多视角知识整理+引用 | 缺引用验证 | ★★★ |
| AI-Scientist (12k) | 端到端实验→论文 | 缺实验自动化 | ★★★★ |
| Agent Laboratory (5.3k) | 文献→实验→写作三段式 | 缺实验环节 | ★★★ |
| LangGraph | 状态持久+检查点 | 当前无检查点 | ★★★ |
| MinerU (opendatalab) | 15个MCP工具 | pdf_ingest只有7引擎 | ★★ |
| PaperQA2 | RAG+页级引用 | 缺RAG检索 | ★★★ |
| PaperDebugger | Overleaf多Agent审查 | 缺独立审查Agent | ★★ |
| SCISKETCH (EMNLP 2025) | 论文→示意图 | 缺自动图表 | ★★★★ |
| NORA | 9 Agent+冷读审查 | Agent间缺结构化I/O验证 | ★★ |

**最近可追赶（6个月内）**：GPT Researcher 的报告生成能力、PaperDebugger 的独立审查Agent、MinerU 的 MCP工具扩展
**中期（1年）**：LangGraph 检查点持久化、STORM 的多视角引用验证
**远期（2年+）**：AI-Scientist 的实验自动化、SCISKETCH 的自动图表生成
