# 03 写 — 论文写作

## 负责什么
论文草稿、写作模板、段落素材、写作脚本。基于 200+ GitHub 项目调研整合的中文学术写作能力系统。

## 放什么
- 论文草稿 (初稿/修改稿/终稿)
- 写作模板 (中英文)
- 段落素材和句式库
- 写作 prompt 和检查清单
- 写作辅助脚本

## 不放什么
- 论文阅读笔记和复盘 → 01_读_论文阅读与复盘
- 组会 PPT → 04_组会PPT
- 图表生成 → 02_作图与分析

## 核心脚本
- `00_core_scripts/` — 写作自动化脚本 (原 write/scripts/)
- `prompts/` — 写作提示词 (01-12原有 + 13-16新增AI整篇写作)
- `checklists/` — 写作质量检查清单

材料完整性检查报告默认只保留输入文件名，不记录本机绝对路径；这不表示材料本身可以公开，稿件、数据、审稿意见与个人信息仍须按项目权限管理。

## AI整篇论文写作工作流（2026-06-11新增）
- `AI整篇论文写作工作流/README.md` — 模块总览和使用说明
- `AI整篇论文写作工作流/full_paper_generation_workflow.md` — 9步整篇生成工作流
- `AI整篇论文写作工作流/section_by_section_generation_workflow.md` — 分章节生成工作流
- `AI整篇论文写作工作流/gis_thesis_structure_template.md` — GIS/遥感/DEM论文结构模板
- `AI整篇论文写作工作流/anti_academic_fraud_checklist.md` — 防学术造假检查清单
- `AI整篇论文写作工作流/citation_and_evidence_audit.md` — 引用与证据链核查
- `AI整篇论文写作工作流/ai_detector_diagnostic_workflow.md` — AI检测器诊断工作流
- `AI整篇论文写作工作流/anti_ai_tone_quality_checklist.md` — 降AI腔质量清单
- `AI整篇论文写作工作流/writing_process_trace_template.md` — 写作过程留痕模板
- `AI整篇论文写作工作流/日常使用简版提示词.md` — 可直接复制使用的日常提示词

## 新增提示词
- `prompts/13_整篇论文初稿生成_prompt.md` — 整篇论文初稿生成
- `prompts/14_降AI腔但不造假_prompt.md` — 降低AI腔（不造假）
- `prompts/15_AI检测器结果诊断_prompt.md` — AI检测器结果诊断
- `prompts/16_防学术造假审计_prompt.md` — 防学术造假审计
- `checklists/` — 写作质量检查清单
- `skills/` — 写作专用 Skill

## 与其他板块的边界
- 本板块从 01_读 获取论文素材
- 本板块输出供 04_组会PPT 使用
- 写作模板仅用于论文，不适用于 PPT
