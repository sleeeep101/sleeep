# 写作任务路由

> Prompt ID: 00
> 用途: 根据用户输入判断调用哪个写作能力
> 生成方式: write_integration_core.py 自动生成
> AI 辅助草稿，需人工复核。不得伪造数据、实验、结果、引用。

---

## 任务路由表

根据用户输入的关键词或任务描述，路由到对应的 Prompt 文件：

| 用户输入关键词 | 路由文件 | 说明 |
|-------------|---------|------|
| 错别字、语病、语法、纠错、的地得、标点、口语化、空泛词 | `01_chinese_grammar_check.md` | 中文语病检查 |
| 润色、改写、学术化、表达优化、摘要优化 | `02_academic_polish_chinese.md` | 学术润色 |
| 逻辑、论证、因果、概念、推理 | `03_logic_and_argument_check.md` | 逻辑论证检查 |
| 模板化、套话、AI腔、机械感、空洞 | `04_reduce_template_style.md` | 减少模板化表达 |
| 文献综述、综述、research gap、脉络、方法比较 | `05_literature_review_builder.md` | 文献综述 |
| 摘要、引言、方法、结果、讨论、结论、章节 | `06_abstract_intro_method_result_discussion.md` | 论文各章节 |
| GIS、遥感、空间分析、地理、地图、ArcGIS、卫星 | `07_gis_remote_sensing_academic_style.md` | GIS/遥感表达 |
| 组会、PPT、汇报、周报、导师 | `../组会/prompts/08_group_meeting_outline.md` | 组会提纲 |
| 追问、问题、导师问 | `../组会/prompts/09_advisor_question_generator.md` | 导师追问 |
| 引用、参考文献、citation、reference | `10_reference_and_citation_check.md` | 参考文献检查 |
| docx、pdf、格式、排版、输出 | `11_markdown_to_docx_pdf_check.md` | 输出格式检查 |
| 写作学习、句式、卡片 | `12_writing_learning_card.md` | 写作学习卡片 |
| 整篇生成、初稿、全文草稿、全篇、材料准备 | `13_整篇论文初稿生成_prompt.md` | 整篇论文初稿生成 |
| 降AI腔、去AI味、自然化、不像AI、表达具体 | `14_降AI腔但不造假_prompt.md` | 降低AI腔 |
| AI检测、检测器、GPTZero、AIGC检测、误判 | `15_AI检测器结果诊断_prompt.md` | AI检测器诊断 |
| 学术造假、造假检查、文献核查、数据核查、诚信审计 | `16_防学术造假审计_prompt.md` | 防学术造假审计 |

## 使用方式

输入你的论文草稿或写作需求，系统会自动识别任务类型并路由到对应 Prompt。
如果你不确定该用哪个，直接描述你的需求即可。

> 组会相关内容已统一归入 `../组会/`，write 只保留写作能力和跨模块路由说明。
