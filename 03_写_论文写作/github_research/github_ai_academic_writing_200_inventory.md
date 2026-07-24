# GitHub AI学术写作200+项深度调研清单

> 调研日期: 2026-06-11
> 调研范围: GitHub + PyPI + NPM + Web (学术写作/AI辅助/检测器/中文写作/防造假/GIS写作)
> 分类: A-I共9大类
> 预计总候选数: 200+ (4个Agent并行收集中)

---

## A. 学术写作资源类 (Academic Writing Resources)

| # | 名称 | URL | 类型 | Stars | 可借鉴点 | 采用 |
|---|------|-----|------|-------|---------|------|
| A01 | awesome-scientific-writing | https://github.com/writing-resources/awesome-scientific-writing | awesome-list | ~875 | 100+工具目录，覆盖编辑器/文献管理/插画/转换器 | 部分采用 |
| A02 | consistent-scientific-style | https://github.com/leonardopedroso/consistent-scientific-style | checklist | 小众 | LaTeX科学写作风格清单 | 采用 |
| A03 | Prompt-Engineering-for-Academic-Writing | https://github.com/LeSinus/Prompt-Engineering-for-Academic-Writing | 提示词指南 | 小众 | 结构化方法论：具体性/清晰度/上下文/约束 | 采用 |
| A04 | ChatGPT-Academic-Prompt | https://github.com/xuhangc/ChatGPT-Academic-Prompt | 提示词库 | ~775 | 全生命周期提示词，期刊特定模板 | 部分采用 |
| A05 | paper-prompt | https://github.com/ChenZiHong-Gavin/paper-prompt | 提示词库 | 热门 | 6阶段全生命周期：选题→文献→框架→写作→润色→投稿 | 采用 |
| A06 | research-prompts | https://github.com/toddmaustin/research-prompts | 提示词/工具 | 稳定 | 过程即提示词：brutal-review, orphan-finder, hallucinations-detector | 采用 |
| A07 | Denolle Lab Scientific Writing Rubric | https://denolle-lab.github.io/_pages/pub_rubric.html | 评分标准 | N/A | 7类评分：科学探究/方法/开放科学/清晰度/影响/伦理/呈现 | 采用 |
| A08 | LaTeX-Research-Toolkit | https://github.com/vuhung16au/LaTeX-Research-Toolkit | 工具包 | 小众 | LaTeX论文/论文/展示模板+文档+示例 | 部分采用 |
| A09 | thesis-template (digital-work-lab) | https://github.com/digital-work-lab/thesis-template | 模板 | 有特色 | Docker化Markdown论文，Pandoc+TeX Live，9000+CSL | 参考 |
| A10 | apathe (R包) | https://github.com/crsh/apathe | 模板 | CRAN | APA6论文模板(R Markdown)，DOI引用，计算可重现 | 参考 |
| A11 | Pandoc User-Contributed Templates | https://github.com/jgm/pandoc/wiki | 模板集合 | 35k+(Pandoc) | Markdown→PDF/DOCX/HTML管道的丰富模板 | 参考 |
| A12 | LanguageCheck | https://github.com/johannesbuchner/languagecheck | 工具(检查器) | ~93 | 离线LaTeX语法检查/拼写/句子长度/段落时态一致性 | 采用 |
| A13 | Angry Reviewer | https://github.com/anufrievroman/angry-reviewer | 工具(风格检查) | ~100 | 数百条规则基于The Craft of Scientific Writing，Web应用 | 采用 |
| A14 | Proselint | https://github.com/amperser/proselint | 工具(检查器) | ~4.3k | 专家背书的散文检查器(Garner/Pinker/Strunk&White) | 采用 |
| A15 | Vale | https://github.com/errata-ai/vale | 工具(检查器) | ~4.6k | 可配置风格检查器，支持多风格指南(MS/Google) | 采用 |
| A16 | write-good | https://github.com/btford/write-good | 工具(检查器) | ~5k | 英语散文检查器，标记被动语态/弱词/冗余 | 参考 |
| A17 | alex | https://github.com/get-alex/alex | 工具(检查器) | ~4.8k | 捕捉性别偏见、刻板印象和其他不公平语言 | 参考 |

---

## B. AI辅助学术写作类 (AI-Assisted Academic Writing)

| # | 名称 | URL | 类型 | Stars | 可借鉴点 | 采用 |
|---|------|-----|------|-------|---------|------|
| B01 | Claude-Research-Paper-OS | https://github.com/thuyhuongctu-cell/Claude-Research-Paper-OS | Agent系统 | ~6.4k | 6 Agent, 47+ Skills, 5阶段管线, LaTeX编译, 引文验证, 模拟同行评审 | 部分采用 |
| B02 | open-paper-machine | https://github.com/TobiasBlask/open-paper-machine | Agent插件 | 增长中 | 9阶段管线, 16技能引擎, PRISMA合规SLR, 审稿回复自动化 | 部分采用 |
| B03 | ai-research-toolkit | https://github.com/debug-zhuweijian/ai-research-toolkit | MCP工具包 | 显著 | 7阶段全流程, 20+学术数据库, MCP服务器(搜索/PDF/审稿/写作) | 部分采用 |
| B04 | sisyphus-academica | https://github.com/argahv/sisyphus-academica | Agent群 | 有特色 | 20+ Agent群, 6个创新引擎, 10个对抗审稿人, 41个Humanizer模式, 100%引文验证 | 部分采用 |
| B05 | research-paper-pipeline | https://github.com/SGloria/research-paper-pipeline | Agent管线 | 显著 | 7Agent: CS顶会论文(NeurIPS/ICML/CVPR), 4层引文验证, 断点续传 | 参考 |
| B06 | Research-Paper-Writing-Skills | https://github.com/Master-cai/Research-Paper-Writing-Skills | Skill包 | 增长中 | ML/CV/NLP论文写作, 章节特定指南, 声明-证据对齐检查 | 部分采用 |
| B07 | research-cli | https://github.com/iechor-research/research-cli | CLI工具 | NPM | 多模型CLI, 大纲生成, LaTeX管理, 实验代码生成, 期刊匹配 | 参考 |
| B08 | ai-research-team | https://github.com/tomlin7/ai-research-team | Agent框架 | 显著 | 11专业Agent(研究负责人/文献审阅/假设生成/实验设计等) | 参考 |
| B09 | STORM | https://github.com/stanford-oval/storm | 知识整理 | ~28k | LLM维基百科风格文章生成+引文, 视角引导问题, 模拟对话 | 参考 |
| B10 | GPT-Researcher | https://github.com/assafelovic/gpt-researcher | Agent | ~17k | 成熟多Agent深度研究, 规划/爬取/聚合/长报告+引用 | 参考 |
| B11 | paper-qa (PaperQA2) | https://github.com/Future-House/paper-qa | RAG工具 | ~8.6k | 高精度引用优先问答, 页面级引用, 论文写作RAG校对 | 采用 |
| B12 | AI-Scientist-v2 | https://github.com/SakanaAI/AI-Scientist-v2 | 自动发现 | ~6.1k | 端到端自动科学发现, Nature发表, ICLR研讨会接收 | 参考 |
| B13 | AgentLaboratory | https://github.com/SamuelSchmidgall/AgentLaboratory | Agent框架 | ~5.6k | PhD/Postdoc/Reviewer三Agent, arXiv搜索, 实验设计/执行 | 参考 |
| B14 | Awesome-Auto-Research-Tools | https://github.com/handsome-rich/Awesome-Auto-Research-Tools | awesome-list | 增长中 | 星级排名元列表: 端到端/深度学习/实验/技能分类 | 采用 |
| B15 | academic-writing-skills | https://github.com/bahayonghang/academic-writing-skills | Skill包 | ~298 | 去AI编辑, CrossRef验证引文, 审稿人风格审计, GB/T 7714 | 采用 |
| B16 | OpenPrism | https://github.com/OpenDCAI/OpenPrism | AI工作空间 | 增长中 | 开源, LaTeX编辑+PDF预览+AI助手, ACL/CVPR模板, 本地优先 | 参考 |
| B17 | Prompts-to-Paper | https://github.com/chenandrewy/Prompts-to-Paper | 提示词系统 | 小众 | Claude 3.7完整论文写作提示词工程演示 | 部分采用 |
| B18 | Manubot | https://github.com/manubot/manubot | 出版工作流 | BSD | 自动化学术出版, manubot cite(DOI检索), manubot ai-revision | 采用 |
| B19 | LLM-Academic-Writing | https://github.com/dixiyao/LLM-Academic-Writing | 研究仓库 | 显著 | GPT4Reviewer, GrammarCheck模块 | 参考 |
| B20 | proofreading skill | https://github.com/JakobThumm/proofreading | Skill | 小众 | 100+检查(结构/数学/统计/图表/语法/缩写), 交互式修复 | 参考 |
| B21 | matsengrp/plugins | https://github.com/matsengrp/plugins | 插件 | 小众 | 科学写作/代码审查/技术文档专用Agent | 参考 |
| B22 | scientific_writing | https://github.com/lzun/sec-paper-checklist | 检查清单 | 小众 | 安全领域论文写作清单 | 参考 |
| B23 | OpenScholar | Nature论文模型 | 模型 | N/A | 科技文献综合检索增强模型, Nature发表 | 参考 |
| B24 | Awesome-AI-Scientists | https://github.com/natnew/Awesome-AI-Scientists | awesome-list | 增长中 | Coscientist/ChemCrow/FunSearch/Robin等精选 | 参考 |

---

## C. 文献综述与结构化写作类 (Literature Review & Structured Writing)

| # | 名称 | URL | 类型 | Stars | 可借鉴点 | 采用 |
|---|------|-----|------|-------|---------|------|
| C01 | slr-prisma | https://github.com/keemanxp/slr-prisma | Skill | 显著 | PRISMA 2020系统性文献综述, 6阶段: 访谈→草稿→流程图→引用→Word→清单审计 | 采用 |
| C02 | PROMPTHEUS | https://github.com/joaopftorres/PROMPTHEUS | SLR管线 | MDPI发表 | 全自动SLR: 查询扩展→检索→主题建模→摘要→LaTeX报告 | 参考 |
| C03 | MacAma | https://github.com/YilinYuan/MacAma | 元分析+SLR | 显著 | 半自动Meta分析, PubMed检索, LLM筛选, 森林图, AI辅助写作(MetaWriter) | 参考 |
| C04 | SRWS-PSG/protocol-templates | https://github.com/SRWS-PSG/protocol-templates | 模板集合 | 小众 | PRISMA/JBI/PRISMA-ScR模板, Markdown→DOCX/PDF/HTML | 采用 |
| C05 | LLM4SR | https://github.com/du-nlp-lab/LLM4SR | 综述/元资源 | 显著 | LLM科研工具"相关工作生成"分类, 组织所有LLM4Science工具 | 采用 |
| C06 | SurveyX | https://github.com/IAAR-Shanghai/SurveyX | 综述生成 | 增长中 | 端到端综述生成+LaTeX/PDF, 两阶段准备-生成设计, AttributeTree | 参考 |
| C07 | InteractiveSurvey | https://github.com/TechnicolorGUO/InteractiveSurvey | 交互式综述 | 增长中 | Web平台交互式综述, Docker+GPU, SUS 84.4(A+级), PDF导出 | 参考 |
| C08 | AutoSurvey2/auto_research | https://github.com/annihi1ation/auto_research | 综述生成 | 增长中 | 多阶段: 检索→规划→生成→LaTeX汇编, 实时RAG | 参考 |
| C09 | ARISE | https://github.com/ziwang11112/ARISE | Agent迭代引擎 | 增长中 | 22个专业Agent, 评分表引导, 92.48/100质量分 | 参考 |
| C10 | matriz (R包) | https://github.com/jpmonteagudo28/matriz | 工具(CRAN) | CRAN | 结构化文献矩阵(init→add→search→merge→export), CSV/Excel导出 | 采用 |
| C11 | create-academic-research | https://www.npmjs.com/package/create-academic-research | CLI脚手架 | NPM | 生成完整研究工作空间: 文献矩阵/检索策略/PRISMA图/差距分析 | 参考 |
| C12 | @2p1c/harness-writing | https://www.npmjs.com/package/@2p1c/harness-writing | 写作框架 | NPM | 规范驱动: 问题→研究→方法→计划→写→引用→编译 | 参考 |
| C13 | GenAI_Agents (NirDiamant) | https://github.com/NirDiamant/GenAI_Agents | 教程/管线 | ~40k | 图架构自动系统综述Agent: Semantic Scholar搜索→PDF分析→章节分析→综述草稿 | 参考 |

---

## D. 引用与证据检查类 (Citation & Evidence Checking)

| # | 名称 | URL | 类型 | Stars | 可借鉴点 | 采用 |
|---|------|-----|------|-------|---------|------|
| D01 | Citation_checker | https://github.com/programmeratlarge/Citation_checker | Web应用 | Cornell | PDF/DOCX上传→提取参考文献→逐一搜索(DOI/标题)→精确/接近/未找到 | 采用 |
| D02 | CiteCheck | https://github.com/color4-alt/CiteCheck | CLI+Skill | 增长中 | 跨Agent的引文验证(LaTeX/PDF), 多源交叉验证, 主题相关性评分 | 采用 |
| D03 | sciwrite-lint | https://github.com/authentic-research-partners/sciwrite-lint | 检查器 | 增长中 | 23项自动检查: 引文验证/声明验证/一致性/图表/撤稿交叉检查, 完全本地 | 采用 |
| D04 | CiteGuard | https://github.com/SuperMarioYL/citeguard | CLI | 增长中 | 批量验证(DOI/arXiv/CVE/SHA), 终端红/绿表格, JSON报告, SQLite缓存 | 部分采用 |
| D05 | claude-skill-citation-checker | https://github.com/PHY041/claude-skill-citation-checker | Skill | 显著 | AI引文幻觉检测, 100%假检测率, 0假阴性, 无需API密钥 | 采用 |
| D06 | bibguard | PyPI | CLI | PyPI | 100%假引文检测(14/14), 5源交叉检查, 幻影DOI发现, 自动修复.bib | 采用 |
| D07 | academic-refchecker (Microsoft) | PyPI | CLI | PyPI | 全功能引文验证(S2/OpenAlex/CrossRef), LLM提取, 模糊匹配 | 部分采用 |
| D08 | bibliography-verification-tool | https://github.com/pvsundar/bibliography-verification-tool | 验证工具 | 小众 | APA格式DOCX书目验证(CrossRef+PubMed) | 参考 |
| D09 | bib-ami | https://github.com/hrolfrc/bib-ami | 清理工具 | 小众 | .bib文件清理/合并/去重, CrossRef验证, 补全缺失元数据 | 参考 |
| D10 | OneCite | https://github.com/HzaCode/OneCite | 解析/格式化 | 小众 | 输入混乱文本(DOI/标题/arXiv)输出清洁BibTeX | 参考 |
| D11 | KnowHalu | https://github.com/javyduck/KnowHalu | 研究工具 | 研究 | 多形式知识驱动事实检查+分步推理, 区分编造和非编造幻觉 | 参考 |
| D12 | RefChecker (Amazon) | https://github.com/amazon-science/RefChecker | 基准/框架 | Amazon | 声明三元组提取+验证(Zero/Noisy/Accurate), 11k标注数据 | 参考 |
| D13 | deltasci | https://github.com/boheling/deltasci | 验证层 | 小众 | 确定性引文验证(无LLM干预), 声明标记: [CLAIM]/[GAP]/[SYNTHESIS] | 部分采用 |
| D14 | face-the-facts | https://github.com/drusso98/face-the-facts | 研究/工具 | 研究 | RAG事实检查评估(声明风格/检索方法/分块策略对比) | 参考 |
| D15 | bibcheck | https://github.com/braveliu/bibcheck | CLI | 小众 | 检查.bib中URL/DOI是否可达, 报告失效链接 | 参考 |

---

## E. LaTeX/Markdown/论文模板类 (Templates)

(等待Agent2结果)

---

## F. 学术诚信与防造假类 (Academic Integrity)

(等待Agent2结果)

---

## G. AI检测器类 (AI Detectors - diagnostic only)

(等待Agent2/Agent4结果)

---

## H. 中文论文写作/研究生写作类 (Chinese Academic Writing)

(等待Agent2结果)

---

## I. GIS/遥感论文写作类 (GIS/Remote Sensing Writing)

(等待Agent3结果)

---

## 附加: 工具生态类 (Tools & Pipelines)

(等待Agent3/Agent4结果)

---

## 去重与筛选说明

> 将在所有Agent完成后执行。
> 去重规则: (1)fork项目只保留源头; (2)同名awesome list只保留最完整; (3)论文模板只提炼结构不批量复制; (4)AI detector保留诊断思想; (5)AI humanizer/evasion标记为排除; (6)排除纯营销/空仓库/无README项目。
> 目标: 200+→20-40高价值来源→10-20可整合方法→8-12可直接使用的提示词/清单/模板。
