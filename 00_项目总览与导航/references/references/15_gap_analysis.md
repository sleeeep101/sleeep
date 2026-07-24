# 15_gap_analysis — 缺口分析与优先级

## 已覆盖环节

| 环节 | 覆盖程度 | 主 Skill |
|------|---------|---------|
| 任务规划 | ✅ 完整 | planning-with-files-zh |
| 文献检索 | ✅ 完整 | academic-search |
| 每日雷达 | ✅ 完整 | 有脚本(daily_paper_curator.py) |
| 单篇阅读 | ✅ 完整 | ljg-paper-flow |
| 引文链追踪 | ✅ 完整 | ljg-paper-river |
| 概念理解 | ✅ 完整 | ljg-think + ljg-learn |
| 周/月综述 | ✅ 完整 | scientific-thinking-literature-review |
| 选题生成 | ✅ 完整 | brainstorming-research-ideas |
| AI Code拆解 | ✅ 完整 | 有模板(06_ai_code_task_template.md) |
| 外部参照系 | ✅ 已补 | GitHub 外部 Skills 调研完成 (11_external_skill_patterns.md) |
| 图表 | ✅ 方案层完整 | academic-plotting (Claude出方案→Codex执行) |
| 学术写作 | ✅ 完整 | paper-spine |
| 审稿检查 | ✅ 完整 | academic-paper-reviewer |
| 投稿返修 | ✅ 完整(后期) | nature-response |
| PPT汇报 | ✅ 完整 | nature-paper2ppt |
| 归档复盘 | ✅ 完整 | research-manager |

## 通过 references 补足的缺口

| 缺口 | 补足方式 | 状态 |
|------|---------|------|
| 论文卡片模板 | 04_paper_card_template.md | ✅ 已补 |
| 知识库结构 | 05_knowledge_base_schema.md | ✅ 已补 |
| 写作句式模板 | 07_writing_templates.md | ✅ 已补 |
| 输出规范 | 09_output_files.md | ✅ 已补 |
| GIS/遥感流程 | 12_gis_remote_sensing_workflow.md | ✅ 已补 |
| CNKI 中文文献 | 13_cnki_chinese_literature_workflow.md | ✅ 已补 |
| 实验可复现 | 14_experiment_reproducibility.md | ✅ 已补 |
| 各环节完成标准 | 16_done_definition.md | ✅ 已补 |
| 论文质量筛选 | 17_paper_quality_filter.md | ✅ 已补 |
| 停损机制 | 18_stop_loss_rules.md | ✅ 已补 |
| 术语/概念库 | 19_concept_glossary.md | ✅ 已补 |
| 导师课题适配 | 20_advisor_topic_fit.md | ✅ 已补 |
| 中英文分工策略 | 21_chinese_english_literature_strategy.md | ✅ 已补 |
| 个人执行节奏 | 22_execution_rhythm.md | ✅ 已补 |
| 文件命名与备份 | 23_file_naming_backup_rules.md | ✅ 已补 |

## 仍然缺的环节

| 缺口 | 严重程度 | 为何重要 | 目前替代方案 |
|------|---------|---------|------------|
| **ArcGIS/QGIS/GEE 实操积累** | 🟡 中 | 完成标准已建立(16)，需日积月累 | 12_gis_... 有框架+完成标准 |
| **术语概念库内容填充** | 🟡 中 | 框架已建(19)，需长期积累 | 19_concept_glossary.md 有初始内容 |
| **学期/年度总结** | 🟢 低 | 月总结已覆盖，学期总结可延后 | 月度总结替代 |
| **知识库可视化/图谱** | 🟢 低 | 非必需 | 不需要 |

## 已放弃/后期再说

| 项目 | 原因 |
|------|------|
| 复杂论文 API/MCP 接入 | 当前只读外网免费论文，arXiv + S2 API 够用 |
| CNKI 自动下载 | 合规风险 + 用户后续手动提供 |
| 付费数据库接入 | 当前不需要，后续通过学校 VPN 手动访问 |
| 自动下载论文脚本 | 可能有合规问题，用户手动下载更安全 |

## 本次更新解决的缺口

| 原缺口 | 解决方案 | 新文件 |
|--------|---------|--------|
| 各环节无完成标准 | 6环节完成标准+模板 | 16_done_definition.md |
| 论文质量无过滤 | 12维评分+5级分类 | 17_paper_quality_filter.md |
| 无停损机制 | 7类停损规则 | 18_stop_loss_rules.md |
| 概念解释散落 | 4大类100+概念初稿 | 19_concept_glossary.md |
| 方向易跑偏 | 4维适配度机制 | 20_advisor_topic_fit.md |
| 中英文混读 | 分工策略+额外字段 | 21_chinese_english_literature_strategy.md |
| 执行无节奏 | 日/周/月节奏+防摆烂 | 22_execution_rhythm.md |
| 文件混乱无备份 | 命名+版本+备份规则 | 23_file_naming_backup_rules.md |
| 写作模板无训练阶梯 | L1-L4渐进训练 | 07_writing_templates.md 更新 |

## 对我最重要的 5 个缺口（优先级排序）

1. **ArcGIS/QGIS/GEE 操作流程模板** — 入学后日常使用，需要标准化的"打开软件→加载数据→分析→导出"流程
2. **写作渐进训练机制** — 不只是一堆模板，而是从"填写句式→仿写段落→独立写作"的阶梯
3. **数据版本管理习惯** — 从研0开始养成，避免研二发现数据乱了
4. **GIS 论文的图表规范模板** — 哪些图该怎么做、图例/配色/比例尺/指北针规范
5. **GitHub 外部调研** — 规格书要求的正式产出

## 暂时不要补的

- 高级实验自动化系统（研二再说）
- 审稿人模拟训练（研二再说）
- Nature 子刊投稿工作流（可能永远用不上）
- 知识图谱/可视化（过度复杂化风险高）
- 自动下载论文脚本（可能有合规问题）

## 未来再说（研二）

- 完整 academic-pipeline 全流程
- 期刊投稿全流程模拟
- LaTeX 模板管理
- 论文预审草稿管理
- 基金申请书模板

## 优先级执行建议

| 阶段 | 重点 |
|------|------|
| 现在（研0） | 建知识库 + 读论文 + 学句式 + GIS 基础 |
| 入学前(2026.08) | 完成 ArcGIS 基础操作 + 读够 30 篇论文 |
| 研一上(2026.09-12) | 跟项目 + 积累方法迁移库 + 练写作 |
| 研一下(2027.01-06) | 开始实验 + 出第一个可复现结果 |
