# 蒸馏来源清单

> 从200+候选中筛选出的高价值来源。仅供方法参考，不批量复制内容。

## 采用（直接整合方法/思想）：37项

### 学术写作工具
1. paper-prompt (ChenZiHong-Gavin) — 6阶段全生命周期提示词
2. research-prompts (toddmaustin) — 过程即提示词方法论
3. LanguageCheck — 离线LaTeX语法/拼写检查
4. Angry Reviewer — 科学写作风格规则
5. Proselint — 专家背书的散文质量检查
6. Vale — 可配置多风格检查器

### AI辅助学术写作
7. academic-writing-skills (bahayonghang) — 去AI编辑+审稿审计+GB/T 7714
8. paper-qa (Future-House) — 高精度引用优先RAG
9. Manubot — 自动化学术出版管线
10. STORM (Stanford) — 视角引导知识整理

### 文献综述
11. slr-prisma — PRISMA 2020系统综述6阶段
12. LLM4SR — LLM科研工具分类组织
13. matriz (R包) — 结构化文献矩阵

### 引用验证（核心）
14. sciwrite-lint — 23项检查(含撤稿交叉检查)，完全本地
15. academic-refchecker (Microsoft) — 引文幻觉检测+LLM搜索
16. CiteGuard — 确定性无LLM快速批量验证
17. CiteCheck — 8源级联交叉验证
18. claude-skill-citation-checker — Agent集成引文验证
19. bibguard — 假引文100%检测
20. CiteTracer — 97.1%精度12类错误分类

### 中文写作
21. Awesome AI Research Writing (Leey21) — 学术提示词库
22. Paper Prompt (ChenZiHong-Gavin) — 论文学术写作提示词
23. SFFAI-AIKT Thesis_Template — 中国大学模板索引
24. latexstudio — 中国LaTeX模板中心

### AI检测器（仅诊断用）
25. lmscan — 离线统计检测(12特征)
26. fast-ai-detector — 可解释性(SAE特征分析)
27. AIGC_text_detector (ICLR 2024) — 多尺度中英双语
28. ImBD (AAAI 2025) — 中文AI文本检测
29. AI Detector Benchmark (mattc95) — 独立基准测试
30. AI Detection Bias Study — 偏差/公平性研究

### 防造假/可重现
31. WORCS — 完整可重现研究R包
32. rrtools — 可重现研究工具包
33. ReproResearch Template — FAIR原则仓库模板
34. AI Disclosure Templates — 多机构AI声明模板

### 写作质量
35. Trinka — 学术专用语法/风格检查(免费层)
36. Writefull — LaTeX感知学术语言编辑
37. Paperpal — Overleaf/Word集成学术写作套件

## 排除项目（明确不采用）

### 检测器对抗/Humanizer（不采用）
- PaperFake — AI检测规避工具
- 快降重 — AI检测规避工具
- harshaneel/humanize — 9个humanization杠杆
- lynote-ai/humanize-text — 多跳翻译规避管线
- prithwiraj84/AI-Humanizer-Pro — Unicode欺骗

### 纯营销/空仓库（不采用）
- 无README、无代码的空仓库
- Star数极低且无实质内容的个人实验项目

### 过度工程化（不采用）
- 需要Docker/K8s/数据库的复杂系统
- 需要多GPU集群的ML训练管线

### 与GIS方向无关（不采用）
- 纯CV/NLP/安全领域特化工具
- 医学/生物信息学专用管线
