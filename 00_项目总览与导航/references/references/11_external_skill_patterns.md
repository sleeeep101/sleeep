# 11_external_skill_patterns — GitHub 外部 Skills 调研

> **2026-07-13 标注**: 本文档为历史调研记录（2026-05-29），引用的 55 个外部 skill 均未安装。
> 当前实际可用 skill 见 `10_skill_inventory_map.md`（13个本地安装）。

## 状态

✅ **已完成** — 2026-05-29，8 类关键词全量搜索，共评估 40+ 仓库，提炼 10 个通用设计模式。

---

## 一、调研概览

| 类别 | 搜索数 | 高相关 | 值得整合 |
|------|--------|--------|---------|
| A. 学术论文阅读 | 12 | 5 | 2 |
| B. 文献综述 | 8 | 4 | 1 |
| C. 学术写作 | 10 | 4 | 4 |
| D. AI Code / Baseline | 6 | 3 | 3 |
| E. 知识库 | 8 | 3 | 1 |
| F. PDF 处理 | 6 | 2 | 1 |
| G. Agent 工作流 | 8 | 4 | 3 |
| H. GIS/遥感 | 6 | 4 | 2 |

---

## 二、高相关仓库评估

### A. 学术论文阅读类

#### A1. PaperOrchestra — ⭐ ~500 · `Ar9av/PaperOrchestra`
- **论文**: arXiv:2604.05018 (Google, 2026)
- **定位**: 多智能体论文写作技能包（Claude Code/Cursor/Cline 通用）
- **核心**: 7 技能（大纲+图表+文献综述+章节写作+润色+基准测试+自动评分），引用验证（Levenshtein > 0.70），LaTeX 健全检查
- **许可**: MIT
- **评分**: 78/100
- **最值得借鉴**: 引用验证管道（Semantic Scholar + 标题模糊匹配）、技能间接口规范、LaTeX 编译检查
- **与已有重叠**: 与 `paper-spine` + `academic-paper` 写作流程重叠
- **是否整合**: 只参考 — 引用验证和 LaTeX 检查部分

#### A2. paper-reading-zh — ⭐ 新 · `MrGeDiao/paper-reading-zh`
- **定位**: 中文论文精读规则包，面向 Codex/Claude Code/Claude Project
- **核心**: 证据规则（未核验不补、读不到不编、比较前先对齐口径），三种阅读模式（深读/工程拆解/调研比较），含真实 PDF 验证记录
- **许可**: MIT
- **评分**: 82/100
- **最值得借鉴**: **证据标注体系（R0/R1/R2）**：未核实=保留占位、找到原句=引用、找到实验数据=确认。直接可迁移到 paper_card_template
- **与已有重叠**: 与 `ljg-paper-flow` + `04_paper_card_template` 重叠
- **是否整合**: **参考** — 证据标注体系，可加入 `04_paper_card_template.md`

#### A3. Paperflow — ⭐ ~200 · `shiml20/Paperflow`
- **定位**: 本地优先论文阅读工作台，DeepSeek 驱动
- **核心**: 动态分块全文阅读、论文范围 Agent 对话、R0/R1/R2 可信度等级、Obsidian 知识库导出
- **评分**: 75/100
- **最值得借鉴**: PDF → 分块 → 逐段 Agent 对话的阅读流程；Obsidian 导出格式

#### A4. paper-reading-agent — `HaoliangCheng/paper-reading-agent`
- **核心**: 6 阶段流水线（上传→快速扫描→阶段路由→构建上下文→Agent 循环→流式响应）
- **技术**: React + Flask + SQLite + Gemini
- **评分**: 68/100
- **最值得借鉴**: 阶段路由设计（背景/方法论/数学/代码四通道）

#### A5. Bryce199805/paper-skills — `Bryce199805/paper-skills`
- **核心**: CV/ML/DL 便携式技能（paper-read + paper-review），多 CLI 适配器清单
- **评分**: 65/100
- **最值得借鉴**: 多 CLI 适配模式

### B. 文献综述类

#### B1. LiRA — `lira-workflow/auto-review-writing` (arXiv:2510.05138)
- **核心**: LangGraph 多智能体，大纲起草→子节写作→编辑→审稿，FAISS 论文检索，引用幻觉缓解（全标题锚定）
- **评分**: 80/100
- **最值得借鉴**: **引用幻觉缓解机制**（先全标题引用 → 最后替换为编号）、子节级论文检索

#### B2. ARISE — `ziwang11112/ARISE`
- **核心**: 模块化智能体（主题扩展+引文策展+文献总结+草稿+同行评审），评分准则驱动的迭代优化
- **评分**: 78/100
- **最值得借鉴**: 评分准则驱动的多轮审稿循环

#### B3. LatteReview — 论文 arXiv:2501.05468
- **核心**: Python 异步框架，标题/摘要筛选+相关性评分+结构化数据提取，RAG 集成，Pydantic 验证
- **评分**: 72/100
- **最值得借鉴**: 异步并行审稿、Pydantic 结构化验证

#### B4. ResearchAgent — `JinheonBaek/ResearchAgent` (NAACL 2025)
- **核心**: 文献扎根的迭代式研究想法生成，Semantic Scholar API，5 维并行评审
- **评分**: 70/100
- **最值得借鉴**: 5 维并行评审指标

### C. 学术写作类

#### C1. academic-research-skills (ARS) — ⭐ 6,400 · `Imbad0202/academic-research-skills`
- **定位**: Claude Code 技能包，当前最完整的学术研究流水线
- **核心**: 4 大模块（Deep Research 13 Agent + Academic Paper 12 Agent + Academic Paper Reviewer 7 Agent + Academic Pipeline 10 阶段）
- **亮点**: 引用验证（Semantic Scholar + Levenshtein > 0.70）、7 项 AI 失败模式检查清单（源自 2026 Nature 论文）、反谄媚协议、三层数据隔离
- **成本**: 1.5 万字论文约 $4-6
- **许可**: MIT
- **评分**: 90/100 — **最高分**
- **最值得借鉴**: 
  1. **7 项 AI 失败模式检查清单**（直接可加入 `08_review_checklists.md`）
  2. **反谄媚协议**：要求 Reviewer 必须找到至少 1 个实质性问题
  3. **三层数据隔离**：raw/ → processed/ → output/
  4. **质量门禁**：每阶段出站前过完整性检查
- **与已有重叠**: 与 academic-workflow 整体重叠度高，但设计更成熟
- **是否整合**: **重点参考** — 7 项失败模式 + 反谄媚协议 + 三层数据隔离

#### C2. OpenDraft — ⭐ ~400 · `federicodeponte/opendraft`
- **核心**: 19 个专业 Agent，20k+ 字论文草稿 10 分钟生成，CrossRef/OpenAlex/SemanticScholar/arXiv 四源交叉验证引用
- **许可**: MIT · 免费（自托管 $0.35/篇 Gemini Flash）
- **评分**: 82/100
- **最值得借鉴**: **四源交叉验证引用**（CrossRef + OpenAlex + SemanticScholar + arXiv），比单一源可靠得多

#### C3. AI-Scientist — ⭐ 2,400 · `SakanaAI/AI-Scientist`
- **核心**: 端到端自动化科学发现（构思→实验→分析→写论文→审稿），支持 Claude/GPT
- **评分**: 85/100
- **最值得借鉴**: 审稿-反驳-再实验反馈闭环

#### C4. STORM — Stanford OVAL
- **核心**: Wikipedia 风格长文生成，多角度提问+多源信息整合
- **评分**: 75/100
- **最值得借鉴**: 多角度提问策略

### D. AI Code / Baseline 类

#### D1. AutoReproduce — `AI9Stars/AutoReproduce` (ACL 2026)
- **核心**: 多智能体框架，自动复现 AI 实验，"论文谱系"算法挖掘引用中的隐性知识，ReproduceBench 基准
- **性能**: 比基线高 70%+，与官方实现差距仅 ~22%
- **评分**: 85/100
- **最值得借鉴**: **论文谱系算法**（从引用链中提取实现细节）、ReproduceBench 评估方法论

#### D2. PaperBench — OpenAI (ICML 2025)
- **核心**: 20 篇 ICML 2024 Spotlight/Oral，8,316 个可评分任务，Claude 3.5 Sonnet 仅 21.0% 复现得分
- **评分**: 88/100
- **最值得借鉴**: **8316 个细分任务的评分标准设计**、与原作者共同制定的评分准则

#### D3. SciReplicate-Bench — `xyzCS/SciReplicate-Bench`
- **核心**: 100 个 NLP 论文算法复现任务，最佳 LLM 仅 39% 执行准确率
- **评分**: 72/100
- **最值得借鉴**: 论文算法到代码的标准化拆解流程

### E. 知识库类

#### E1. second-brain (NicholasSpisak) — ⭐ 291
- **核心**: LLM 维护的个人知识库，raw/ → wiki/ 合成，自动生成交叉引用
- **评分**: 75/100
- **最值得借鉴**: **三层架构**：raw/（原始素材）→ wiki/（AI 结构化页面）→ 自动交叉引用

#### E2. LLMWiki 模式 (Karpathy)
- **核心**: `raw/` → `wiki/` 自动合成，分为 entities/concepts/sources/syntheses 四区
- **评分**: 82/100
- **最值得借鉴**: 四区分类法（实体/概念/来源/综合）、Git 版本控制的纯 Markdown

#### E3. Obsidian + Smart Connections — ⭐ 4,300
- **核心**: 语义向量嵌入笔记链接，支持 Ollama 本地模型
- **评分**: 68/100
- **最值得借鉴**: 本地向量嵌入做去重和相似笔记发现

### F. PDF 处理类

#### F1. anthropics/skills — ⭐ 134,700 · Anthropic 官方
- **核心**: 68 个生产级 Agent Skills，含 PDF 解析、网页搜索、代码执行
- **评分**: 95/100
- **最值得借鉴**: **Skills 标准格式**（YAML frontmatter + 指令体 + 测试用例 + Schema 定义）

#### F2. Prismer — ⭐ 832 · `Prismer-AI/Prismer`
- **核心**: 开源学术研究平台，AI-native PDF Reader + LaTeX Editor + 引用验证 + 多智能体编排
- **评分**: 80/100
- **最值得借鉴**: 全流程平台设计理念（覆盖读→写→发表）

### G. Agent 工作流类

#### G1. CrewAI — ⭐ 34,000 · `crewAIInc/crewAI`
- **核心**: Python 多智能体自动化框架，Crews（自主协作）+ Flows（事件驱动编排）
- **评分**: 85/100
- **最值得借鉴**: 角色分配（研究员/编码员/审稿人）+ 事件驱动流程控制

#### G2. cmbagent — ICML 2025 · `CMBAgents/cmbagent`
- **核心**: ~30 个 LLM Agent，Planning & Control 策略，PhD 级宇宙学任务 78% 成功率
- **评分**: 82/100
- **最值得借鉴**: **Planner + Plan Reviewer 双层规划** + Controller Agent 分发

#### G3. FLOW — ICLR 2025 · `tmllab/2025_ICLR_FLOW`
- **核心**: AOV DAG 图表示工作流，动态优化，并行执行
- **评分**: 78/100
- **最值得借鉴**: 工作流模块化度量（P_avg 并行度 + C_dependency 依赖复杂度）

#### G4. DeepResearchAgent — ⭐ 3,100 · `SkyworkAI/DeepResearchAgent`
- **核心**: 层级式多智能体，顶层规划→专业子智能体执行
- **评分**: 80/100
- **最值得借鉴**: 层级任务分解

### H. GIS/遥感类

#### H1. GIS Copilot v1.0 — Penn State GIBD Lab
- **核心**: 自然语言驱动 QGIS，Agent 自动规划→生成 Python→执行，100+ benchmark 案例
- **评分**: 85/100
- **最值得借鉴**: **GIS 任务的标准化拆解**（自然语言 → 工具链 → 代码生成 → 结果验证）

#### H2. AutonomousGIS GeoData Retriever — Penn State · `Teakinboyewa/AutonomousGIS_GeodataRetrieverAgent`
- **核心**: 自然语言→数据源选择→代码生成→QGIS 加载，plug-and-play 数据源扩展
- **评分**: 80/100
- **最值得借鉴**: **数据源的 plug-and-play 架构**，用户可自行添加新数据源

#### H3. LandTalk.AI — `juergenlandauer/LandTalk.AI`
- **核心**: QGIS 插件，框选区域→截图→Gemini/GPT-4o 多模态分析
- **评分**: 72/100
- **最值得借鉴**: 遥感影像+多模态 AI 的交互分析模式

#### H4. TerraStackAI GeoStudio — `terrastackai/geospatial-studio-toolkit`
- **核心**: Python SDK + QGIS 插件，预置野火/洪涝制图案例，支持超参数优化+模型微调
- **评分**: 78/100
- **最值得借鉴**: 预置灾害案例的模板化设计

---

## 三、提炼的 10 个通用设计模式

### 模式 1：SKILL.md 指令体（非代码）
- **来源**: anthropics/skills、ARS、PaperOrchestra
- **核心**: Skill = YAML frontmatter + Markdown 指令 + references/ 模板，不嵌入 LLM 调用
- **academic-workflow 已实现**: ✅ SKILL.md + references/ 结构完整
- **可改进**: 增加 YAML frontmatter（name/description/version）

### 模式 2：证据等级标注（R0/R1/R2）
- **来源**: paper-reading-zh、Paperflow
- **核心**: R0=未核实保留占位、R1=找到原句引用、R2=找到实验数据确认
- **academic-workflow 已实现**: ⚠️ 仅有"未确认"标注，无分级
- **可改进**: 在 `04_paper_card_template.md` 中加入 R0/R1/R2 证据等级

### 模式 3：引用交叉验证管道
- **来源**: ARS、OpenDraft
- **核心**: Semantic Scholar + CrossRef + OpenAlex + arXiv 四源交叉验证，Levenshtein > 0.70 判定匹配
- **academic-workflow 已实现**: ⚠️ 仅 SQLite 去重，无引用真实性验证
- **可改进**: 在 Codex 任务中加入引用验证脚本

### 模式 4：反谄媚协议
- **来源**: ARS（源自 2026 Nature 论文）
- **核心**: Reviewer 必须找到至少 1 个实质性问题，禁止"good paper, accept"
- **academic-workflow 已实现**: ❌ 无
- **可改进**: 加入 `08_review_checklists.md`

### 模式 5：知识库三层架构
- **来源**: second-brain、LLMWiki
- **核心**: raw/（原始素材）→ wiki/（AI 结构化）→ 自动交叉引用
- **academic-workflow 已实现**: ⚠️ 有 raw→卡片→知识库，但缺少 auto cross-ref
- **可改进**: 术语概念库已建，后续可加自动交叉引用

### 模式 6：Planning & Control 双层编排
- **来源**: cmbagent、FLOW、CrewAI
- **核心**: Planner 拆解任务 → Plan Reviewer 审核 → Controller 分发 → 专业 Agent 执行
- **academic-workflow 已实现**: ✅ 路由表 + 主/辅 Skill 模式
- **可改进**: 增加"Plan Reviewer"独立检查步骤

### 模式 7：质量门禁（Stage Gate）
- **来源**: ARS（Academic Pipeline 10 阶段）
- **核心**: 每阶段出站前过完整性检查（检查清单），不通过不回退→重新走本阶段
- **academic-workflow 已实现**: ✅ `16_done_definition.md`（完成标准）
- **可改进**: 增加显式的"门禁检查"输出字段

### 模式 8：停损/防无限循环
- **来源**: crewAI、cmbagent
- **核心**: 3 次失败→降级为人工介入；不确定性超过阈值→停止
- **academic-workflow 已实现**: ✅ `18_stop_loss_rules.md` 全面覆盖
- **可改进**: 已较完善

### 模式 9：多模态 GIS 交互
- **来源**: GIS Copilot、LandTalk.AI
- **核心**: 自然语言→Agent 规划→GIS 代码生成→执行→结果验证
- **academic-workflow 已实现**: ⚠️ `12_gis_remote_sensing_workflow.md` 有框架但偏静态
- **可改进**: 后续加入 GIS Agent 代码生成模板

### 模式 10：中文论文独立处理管道
- **来源**: paper-reading-zh
- **核心**: 中文论文 ≠ 英文论文的翻译，有独立的写作句式、案例体系、数据处理流程
- **academic-workflow 已实现**: ✅ `21_chinese_english_literature_strategy.md` + `13_cnki_*.md`
- **可改进**: 已较完善

---

## 四、对 academic-workflow 的建议优先级

| 优先级 | 改进项 | 来源 | 影响文件 |
|--------|--------|------|---------|
| 🔴 高 | 证据等级标注 R0/R1/R2 | paper-reading-zh | `04_paper_card_template.md` |
| 🔴 高 | 7 项 AI 失败模式 + 反谄媚协议 | ARS | `08_review_checklists.md` |
| 🟡 中 | 引用交叉验证管道（四源） | ARS + OpenDraft | 新增 AI Code 任务 |
| 🟡 中 | YAML frontmatter 标准化 | anthropics/skills | `SKILL.md` 及各 reference |
| 🟡 中 | Plan Reviewer 独立检查 | cmbagent | `01_skill_router.md` |
| 🟢 低 | GIS Agent 代码生成模板 | GIS Copilot | `12_gis_remote_sensing_workflow.md` |
| 🟢 低 | 自动交叉引用（知识库内） | LLMWiki | `05_knowledge_base_schema.md` |
| ⚪ 观察 | 三层数据隔离 raw/processed/output | ARS | 后期考虑 |

---

## 五、外部参照系总结

academic-workflow 在以下方面**领先**外部同类项目：
- **停损机制**：几乎没有外部项目做了系统化停损设计
- **导师适配度**：独有，外部项目不针对具体导师和毕业场景
- **中英文分工**：独有，外部项目以英文为主
- **GIS/遥感专属流程**：独有，外部 GIS Agent 项目偏工具执行而非科研方法

在以下方面**可改进**：
- **引用验证**：外部项目有成熟的交叉验证管道 ✅ 已整合 (citation-verifier)
- **AI 失败模式防御**：ARS 的 7 项检查清单是经过实证的 ✅ 已整合
- **证据分级**：R0/R1/R2 比单纯"未确认"更精确 ✅ 已整合
- **Skill 标准化**：YAML frontmatter 是生态趋势 ✅ 已整合

---

## 六、补充分析（第二轮深度调研）

### Paperflow — 证据分级系统（75→85 上调评分）

**R0/R1/R2 精确定义**（比 paper-reading-zh 更完整）：

| 等级 | Paperflow 定义 | 触发条件 |
|------|--------------|---------|
| **R0** | 严格限于当前论文文本；数字声明不推断不跨设置比较 | 默认精读模式 |
| **R1** | 基于外部论文，通过六路搜索（种子/后向/前向/基准/综述/近期）获取；需记录来源论文+期刊+年份+URL | 触发 R1 搜索管线 |
| **R2** | 推断、趋势判断、研究意见；不确定性明确声明；以 `#R2` 标签出现在 Obsidian 导出中 | 综合阶段回填缺失章节 |

**六路 R1 搜索管线**（`r1_search.py`）：种子论文 → 后向引用 → 前向引用 → 基准论文 → 综述论文 → 近期论文。每条 RelatedWorkItem 含 `citation_count`、`influential_citation_count`、`comparison_risk`。

**PDF 分块+Agent 并行对话流程**：
1. PyMuPDF 提取文本块 → 按章节检测分块
2. 首轮快速生成全局摘要（Briefing）
3. 并行分块提取（最多 4 线程），每块带全局摘要上下文
4. 协调器合并去重、回填空缺 R2 声明、保留精确证据引用
5. `EvidenceVerifier` 模糊匹配（SequenceMatcher ≥ 0.82 = exact，≥ 0.55 = page_and_quote）

**Obsidian 导出**：YAML frontmatter + `[!quote]` 证据标注 + `[!warning]` 不确定性标注 + 领域地图（Field Map）模式。

**整合建议**：六路 R1 搜索管线可作为后期 AI Code 任务。PDF 分块并行阅读流程是 `ljg-paper-flow` 的升级方向。

### LiRA — 引用全标题锚定模式（80→85 上调评分）

**核心创新：全标题锚定 + 后处理转换**

整个生成管线中，LLM 被要求使用完整论文标题作为行内引用标记（如 `[Deep Residual Learning for Image Recognition | Attention Is All You Need]`），后续用正则 `adjust_review()` 转换回数字编号。**不要求 LLM 计数数字 ID**——这从根本上杜绝了引用编号错误。

**幻觉清理**：`parse_review()` 将残留括号文本（>4 字符且非数字）替换为 "REDACTED"。

**FAISS 增强检索**：ResearcherAgent 分析每篇参考文献（发现/设计/结果/质量），ContentWriterAgent 用 FAISS 相似度搜索检索每节最相关论文。确保 LLM 从验证过的参考池引用。

**整合建议**：全标题锚定+后处理模式可直接写入 paper_card_template 的"引用标注规则"。

### AutoReproduce — 论文谱系算法（85 评分）

**核心：从引用链中提取隐性知识**

目标论文中隐含的实现细节（架构模式、训练约定）——这些论文假设读者知道但不写出来——通过以下方式提取：
1. ResearchAgent 定位 3 篇最相关参考文献
2. 逐篇搜索 arXiv 标题 → 下载 PDF → 提取 GitHub 链接 → 克隆仓库
3. CodeAgent 选择最相关源文件
4. 双向验证循环：ResearchAgent 写结构化摘要 → CodeAgent 生成代码 → 代码-vs-摘要对齐检查 → 不匹配则 UPDATE 精炼摘要 → 对齐则 SUBMIT

**整合建议**：双向验证循环可借鉴到 Codex 任务模板的验收流程。

### GIS 三件套 — 任务分解模式（已整合到 12_gis_...）

**LLM-Find**：数据源手册（.toml）驱动的 Agent 自动发现 + auto-debug 循环（≤10次）。

**AutonomousGIS**：自然语言→GIS 的 7 步标准分解 + 混合模型策略（高推理用强模型，快速调用用轻模型）。

**LandTalk.AI**：QGIS 框选区域→截图→多模态 LLM 分析→结构化 JSON→矢量化。

已整合到 `12_gis_remote_sensing_workflow.md`（新增第 8/9/10 节）。

### 补充评估：低评分仓库二次判断

| 仓库 | 原评分 | 调整 | 理由 |
|------|--------|------|------|
| Paperflow | 75 | → 85 | R1 六路搜索管线 + EvidenceVerifier 是论文阅读类最佳实现 |
| LiRA | 80 | → 85 | 全标题锚定是引用验证的范式创新，简单有效 |
| LLM-Find | — | → 82 | 数据源手册模式可直接用于 GIS 数据管理 |
| ARISE | 78 | → 84 | 评分准则 JSON 可直接复制用于论文自评；CrewAI 多智能体迭代精炼 |
| ResearchAgent | 70 | → 75 | ProblemValidator 5 维并行评审类可复用 |
| TerraStackAI | 78 | → 76 | 微调→推理 QGIS 管道完整但需 GPU，研0 阶段暂不可用 |
| LandTalk.AI | 72 | → 70 | QGIS 插件实用但不适合学术科研场景 |
| Literature-Review-Automation | 60 | → 55 | Autogen+Groq 的简单串联，结构太简陋 |

### 克隆状态

| 仓库 | 状态 | 文件数 |
|------|------|--------|
| academic-research-skills | ✅ | 853 |
| AI-Scientist | ✅ | 2,326 |
| auto-review-writing (LiRA) | ✅ | 77 |
| AutonomousGIS_GeodataRetrieverAgent | ✅ | 115 |
| AutoReproduce | ✅ | 23 |
| LandTalk.AI | ✅ | 31 |
| Literature-Review-Automation... | ✅ | 3 |
| LLM-Find | ✅ | 40 |
| opendraft | ✅ | 205 |
| paper-reading-zh | ✅ | 17 |
| Paperflow | ✅ | 92 |
| PaperOrchestra | ✅ | 135 |
| skills (anthropics) | ✅ | 394 |
| ARISE | ✅ | 799 (122.5MB) | CrewAI 多智能体迭代 + 评分准则 JSON |
| geospatial-studio-toolkit | ✅ | 108 (20.2MB) | IBM/TerraStackAI 微调→QGIS 管道 |
| ResearchAgent | ✅ | 21 (70.6MB) | NAACL 2025 5 维并行评审 |

---

*第二轮调研完成: 2026-05-29 | 16/16 仓库克隆成功 | 12 项设计模式已提炼整合*
