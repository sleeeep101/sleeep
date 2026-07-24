# 02_research_pipeline — 完整科研流水线

> **2026-07-13 标注**: 本文档为历史流水线设计（含 55 个外部 skill 引用）。
> 当前实际工作流见主 `SKILL.md`「桌面 PDF 批量阅读工作流」章节。

16 步流水线，从规划到归档。每步标注：目标、输入、输出、Skills、检查项、知识库。

---

## 流程总览

```
0.规划 → 1.检索 → 2.每日雷达 → 3.单篇阅读 → 4.引文链 → 5.概念拆解
→ 6.周月综述 → 7.选题 → 8.数据实验 → 9.AI Code → 10.图表
→ 11.写作 → 12.审稿润色 → 13.投稿返修 → 14.PPT汇报 → 15.归档
```

## 0. 任务规划

- **目标**：建立 task_plan.md，防止长任务丢上下文
- **Skills**：planning-with-files-zh, writing-plans, strategic-compact
- **输出**：task_plan.md, findings.md, progress.md
- **检查**：是否超过 3 天？是否需要拆分？是否需要 decision log？

## 1. 文献检索

- **目标**：找到候选论文列表，初筛，检查是否可获取全文
- **Skills**：academic-search, nature-academic-search, read, pdf
- **输出**：candidate_papers.md, open_access_check.md
- **完成标准** (见 `16_done_definition.md`): ≥5 篇候选、每篇有 DOI/URL、标注是否免费、TOP 1-3 选出
- **质量筛选** (见 `17_paper_quality_filter.md`): 12 维评分，总分 ≥ 7.5 精读
- **停损** (见 `18_stop_loss_rules.md`): 搜索超过 30 分钟停止

## 2. 每日论文雷达

- **目标**：每天自动检索 + 生成日报 + 知识卡片
- **Skills**：academic-search, read, pdf（按 03_daily_paper_radar.md 流程）
- **输出**：daily_reports/YYYY-MM-DD.md, paper_cards/ ×1-3
- **检查**：SQLite 去重是否通过？评分是否 > 阈值？

## 3. 单篇论文深度阅读

- **目标**：深度理解一篇论文，生成结构化知识卡片
- **Skills**：ljg-paper-flow, ljg-read, nature-reader, academic-researcher
- **输出**：paper_cards/YYYY-MM-DD_序号.md（完整模板含质量评分、导师适配度、中英文专属字段）
- **完成标准** (见 `16_done_definition.md`): 20字段完整卡片 + 方法启发 + 写作句式
- **质量筛选** (见 `17_paper_quality_filter.md`): 12维评分决定精读/泛读/题录/暂缓/丢弃
- **导师适配** (见 `20_advisor_topic_fit.md`): 四维适配度必填
- **中英文策略** (见 `21_chinese_english_literature_strategy.md`): 英文+方法/中文+案例
- **停损** (见 `18_stop_loss_rules.md`): 30 分钟无价值保留题录

## 4. 引文链追踪

- **目标**：理解研究问题发展脉络，找到研究空白
- **Skills**：ljg-paper-river, academic-search, deep-research
- **输出**：citation_river.md, problem_evolution.md, research_gap.md
- **检查**：是否控制追溯深度（≤5层）？是否标记了关键转折点？

## 5. 概念与方法拆解

- **目标**：把复杂方法讲明白，提炼可迁移核心
- **Skills**：ljg-think, ljg-learn, ljg-rank, academic-researcher
- **输出**：concept_notes.md, method_breakdown.md
- **检查**：是否给出了初学者版？是否标注了 GIS 迁移方式？

## 6. 周/月综述与知识库整理

- **目标**：纸卡片 → 方法库/句式库/任务池，去重压缩，输出周总结
- **Skills**：scientific-thinking-literature-review, deep-research, research-manager
- **输出**：周总结.md, 月度方法库.md, 写作句式库.md, AI_Code任务池.md
- **完成标准** (见 `16_done_definition.md`): 复盘7问全部回答、下周最小任务确定
- **执行节奏** (见 `22_execution_rhythm.md`): 每周六写周总结
- **备份** (见 `23_file_naming_backup_rules.md`): 周总结后备份核心库文件
- **检查**：是否去重？是否压缩了重复内容？是否触发停损信号？

## 7. 选题生成

- **目标**：从知识库中生成可做的硕士选题，评估风险
- **Skills**：brainstorming-research-ideas, creative-thinking-for-research, rigor-reviewer
- **输出**：选题池.md, thesis_risk_check.md
- **检查**：数据可得性？毕业风险？是否适合当前能力？

## 8. 数据与实验设计

- **目标**：设计实验、记录过程、版本管理
- **Skills**：data-analyst, 0-autoresearch-skill, scientific-thinking-scholar-evaluation
- **输出**：experiment_plan.md, experiment_log.md, results_summary.md
- **完成标准** (见 `16_done_definition.md`): 数据来源完整记录、参数固定、流程可复现
- **命名规范** (见 `23_file_naming_backup_rules.md`): 实验文件按要求命名
- **停损** (见 `18_stop_loss_rules.md`): 无数据源不开发
- **检查**：数据来源是否记录？随机种子是否固定？是否防数据泄露？

## 9. AI Code / Codex 任务拆解

- **目标**：论文方法 → Codex 可执行的 MVP 任务包
- **Skills**：writing-plans, documentation-writer, academic-plotting
- **输出**：codex_task.md, README_draft.md
- **检查**：是否 MVP？验收标准是否明确？"不要做什么"是否写了？

## 10. 图表与可视化

- **目标**：先定图表方案，再转 Codex 生成
- **Skills**：academic-plotting, nature-figure → 方案 → Codex 绘图
- **输出**：figure_plan.md, plotting_tasks.md
- **检查**：图表目的是否清楚？是否标注了审稿风险？

## 11. 学术写作

- **目标**：从骨架到初稿，逐步构建
- **Skills**：paper-spine, academic-writing, academic-paper, article-writing
- **输出**：outline.md, draft.md, section_plan.md
- **检查**：是否引文支撑？是否标注了需要查证的地方？

## 12. 审稿与严谨性检查

- **目标**：自审逻辑漏洞、证据不足、过度声称
- **Skills**：academic-paper-reviewer, rigor-reviewer, scientific-thinking-scholar-evaluation
- **输出**：review_report.md, rigor_check.md
- **检查**：是否每条结论有证据？是否标注了修改优先级？

## 13. 投稿与返修 ⚠️ 后期使用

- **目标**：投稿信、逐点回复、引文检查、数据声明
- **Skills**：nature-response, nature-citation, nature-data
- **标注**：⚠️ 研二投稿阶段启用，研0研一暂不使用

## 14. PPT 汇报

- **目标**：论文/项目 → 组会/答辩 PPT 大纲
- **Skills**：nature-paper2ppt, presenting-conference-talks, ljg-present
- **输出**：ppt_outline.md, speaker_notes.md
- **检查**：是否 outline-faithful？是否每页有核心信息？

## 15. 归档与复盘

- **目标**：更新 progress、沉淀知识、记录决策和失败、备份重要文件
- **Skills**：research-manager, strategic-compact, planning-with-files-zh
- **输出**：progress.md 更新, 长期知识库.md 更新, change_log.md 更新
- **备份** (见 `23_file_naming_backup_rules.md`): 核心库文件备份到 backups/
- **防膨胀** (见 `05_knowledge_base_schema.md`): 季度瘦身检查
- **检查**：是否记录了失败尝试？是否标记了"下一步"？是否已备份？

---

## 每阶段出站质量门禁（5 问自查）

来源：academic-research-skills (ARS)。每完成一个 pipeline 阶段，出站前必答 5 问：

1. **引用完整性** — 最新输出中有未核验的引用吗？
2. **谄媚让步** — 本阶段是否无批判地接受了所有反馈？有没有该质疑但没质疑的地方？
3. **质量轨迹** — 本阶段输出质量是否 ≥ 上一阶段？如有下降 → 暂停并标记
4. **范围纪律** — 本阶段是否添加了用户未要求的内容？如有 → 说明原因
5. **完整性** — 本阶段所有必需交付物都存在吗？缺什么？

**阻断规则**：任一问题答案为"否/有/缺" → 暂停推进，先修后继续。
