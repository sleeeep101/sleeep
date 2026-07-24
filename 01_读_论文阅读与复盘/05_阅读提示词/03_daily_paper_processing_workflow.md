# 03 每日论文处理工作流提示词

## 用途

完整的每日论文处理流水线：桌面 PDF → 提取/去重/归档 → 日报生成 → 知识卡片补齐 → 核验。适用于每日定时任务或手动触发。

> 当前 `DailyPaperCurator_1200` 定时任务处于搁置状态；每日产物以本流程的手动/Agent 执行为准。定时任务即使未来恢复，也不能替代第五步的写作技法批次核验和安全收尾。

支持两种模式：
- **全自动模式**：`process_desktop_pdfs_20260623.py`（内置 pdf_ingest 7引擎级联提取 → 去重 → 评分 → 归档）
- **Claude 深度模式**：`pdf-image-text-extractor` skill 提取 → Claude/Agent 精读 → 手动写知识卡片

---

## 提示词

```
请按 academic-workflow 规则执行每日论文处理。先阅读：
1. <REPO_ROOT>/CLAUDE.md (or equivalent project-level rules)
2. <REPO_ROOT>/SKILL.md

任务目标：
1. 处理目标目录（如 Desktop）上今天新增的所有 PDF。
2. 所有桌面 PDF 必须建立 Desktop_PDF_ID、哈希、页数、去重状态、解析状态、证据状态和最终去向。
3. 只有达到 PDF_TEXT_FULL 且通过重复检查的论文，才能写入日报正文、长期知识库、可能的创新点和已读论文清单。
4. 正文证据不足、重复、解析失败或非论文 PDF，不要强行入库，要归档到对应目录并在日报中说明。
5. 最近论文日报卡片要补齐，不按分数过滤；但补卡不等同于正式入库。
6. 完成后检查禁用表达（定义在 00_core_scripts/_shared_constants.py 的 BANNED_EXPRESSIONS），不要留下"仅摘要、待补读、后续处理、详见原文、ABSTRACT_ONLY、PDF_TEXT_PARTIAL"等表达。
7. 论文阅读完成后删除中间提取产物（data/pdf_library/processed/*），PDF原文移至 fulltext_papers/YYYY-MM-DD/。
8. Windows 环境按 win64 处理，不要使用 win32 假设。

今天日期用实际日期 YYYY-MM-DD。

## 方式一：Claude 深度阅读（推荐用于少量重要论文）

第一步，用 pdf-image-text-extractor skill 提取文本：
直接调用 skill，引擎选 pymupdf4llm 或 auto。如果中文编码异常，降级到 easyocr 或 Claude 手动阅读。

第二步，Claude + Agent 精读：
- 用多 Agent 按主题分类并行阅读
- 每篇论文生成 ≥15 行的完整知识卡片
- 卡片必须包含：基本信息/一句话总结/研究问题/数据来源/方法流程/核心方法/创新点/主要结果5点/局限/可迁移GIS的点/价值评分

第二步半，写作技法 + 专业术语提取（A/B级论文必做，不可跳过）：
- 精读完成后，对每篇 A/B 级论文按 05_writing_technique_extraction.md 的 8 维框架逐篇提取写作技法
- 同时提取论文中的领域专业术语（GIS/遥感/DEM/地貌/水土保持），标注中英文全称和缩写
- 技法 → 去重后写入 `04_长期知识库/学术写作技法库.md`
- 术语 → 去重后写入 `04_长期知识库/专业术语库.md`
- 论文卡片不包含技法与术语提取内容，直接入库

第三步，归档和转换：
将桌面 PDF 移至 fulltext_papers/YYYY-MM-DD/，删除中间提取产物。
然后对入库 PDF 批量转 markdown：
```
python -m markitdown "PDF路径" > "D:\ruanjian\123\academic-workflow\01_读_论文阅读与复盘\02_论文阅读库\md\YYYY-MM-DD\论文名.md"
```

脚本批处理完成后必须运行：
```
python "D:\ruanjian\123\academic-workflow\01_读_论文阅读与复盘\00_core_scripts\enrich_archived_pdfs.py" --date YYYY-MM-DD
```
该步骤为归档目录中的每份 PDF 生成可追溯 Markdown，更新 `专业术语库.md`，并依据日报的全文卡片补齐 `已读论文清单.md`。转换失败或数量不一致时不得删除备份。

已读清单由 `00_core_scripts/rebuild_reading_list.py` 重建：它合并日报关联的 Markdown 与归档来源，按标题标准化去重，并区分“日报明确 `PDF_TEXT_FULL`”与“日报关联全文”两类证据。写入后复核行数与内容哈希；仅验证通过才删除本次临时备份。

## 方式二：脚本全自动处理（推荐用于大批量）

第一步，安全预览：
python "D:\ruanjian\123\academic-workflow\01_读_论文阅读与复盘\00_core_scripts\process_desktop_pdfs_20260623.py" --date YYYY-MM-DD --dry-run

第二步，正式处理（内置 pdf_ingest 7引擎提取 → 去重 → 评分 → 归档 → 日报）：
python "D:\ruanjian\123\academic-workflow\01_读_论文阅读与复盘\00_core_scripts\process_desktop_pdfs_20260623.py" --date YYYY-MM-DD

第三步，补齐知识卡片：
python "D:\ruanjian\123\academic-workflow\01_读_论文阅读与复盘\00_core_scripts\backfill_daily_paper_cards.py" --date YYYY-MM-DD

回补最近 7 天：
python "D:\ruanjian\123\academic-workflow\01_读_论文阅读与复盘\00_core_scripts\backfill_daily_paper_cards.py" --days 7 --date YYYY-MM-DD

第四步，写作技法提取（A/B级论文必做，不可跳过；这是收尾硬关卡）：
- 脚本处理完成后，Claude 对当日 A/B 级论文逐篇提取写作技法
- 按 05_writing_technique_extraction.md 的 8 维框架分析
- 提取后先检索 04_长期知识库/学术写作技法库.md 去重，再写入
- 论文卡片不包含技法提取内容，直接入库
- 只记"怎么用"，不抄整句整段

第五步，登记并安全收尾（必须执行）：
- 每日必须交付并核验：`日报`、`长期知识库`、`学术写作技法库`、`专业术语库`、`md/YYYY-MM-DD/` 全文归档、`已读论文清单`。
- 当日存在 `PDF_TEXT_FULL` 论文时，批处理一律显示“待写作技法批次核验”并保留临时备份；即使同日已有旧标记也不能自动删除，避免重复运行借用旧标记。不得报称完成。
- 写作技法和术语已实际入库后，执行以下命令登记覆盖数量并复核全部产物；只有日报、长期知识库、写作技法库、专业术语库、Markdown（数量/哈希/乱码）和已读清单都通过，才会删除**该日期**的临时备份：

```powershell
python "D:\ruanjian\123\academic-workflow\01_读_论文阅读与复盘\00_core_scripts\finalize_daily_reading_batch.py" --date YYYY-MM-DD --covered-paper-count X --new-techniques X --merged-techniques X
```

完成后必须核验：
1. 目标目录是否还残留 PDF。
2. fulltext_papers/YYYY-MM-DD/ 下三个目录数量是否与处理总数一致：
   - 每日论文源数据文件（入库论文）
   - 重复文件_已核验（SHA256/题名重复）
   - 未入库_已检查（证据不足）
3. YYYY-MM-DD_论文阅读日报.md 是否包含桌面 PDF 全量处理台账。
4. 桌面 PDF 台账数量是否等于当日扫描 PDF 数。
5. 卡片补齐区的"补齐文件数"是否等于实际补充知识卡片数量。
6. **写作技法提取 = 当日 A+B 级论文全量覆盖，每篇必提取，不得跳过任何一篇**。
6.5 **专业术语提取 = 当日 A+B 级论文全量覆盖，每篇至少 3 个术语，不得跳过任何一篇**。
7. 禁用表达残留为 0；如有残留，先修复再汇报。
8. **六项交付物齐全**：日报、长期知识库、写作技法库、专业术语库、`md/YYYY-MM-DD/` 全文归档、已读论文清单；并确认收尾命令返回 `backup_cleaned: true`。否则只能汇报“待收尾”，不得称已完成。

最终回复用中文，必须给出精确数字：

## 一、PDF 处理概况
- 桌面 PDF 总数、归档数量、重复数量、未入库数量、PDF_TEXT_FULL 数量。
- 日报卡片补齐数量。
- 禁用表达检测结果。

## 二、写作技法库入库情况（必须包含）
- **分析论文数**：当日实际提取了技法的论文数
- **跳过论文数**：模板化短文/证据不足等原因跳过的论文数
- **新增技法**：X 条（列出技法编号和简要描述）
- **合并技法**：Y 条（列出合并到哪条已有技法）
- **覆盖类别**：本次覆盖了 8 类中的哪几类
- **未覆盖类别**：哪些类别本次无新技法（简要说明原因）
- **技法库当前总量**：总技法数 / 覆盖论文数

## 三、专业术语库入库情况（必须包含）
- **新增术语**：X 条（列出术语ID和名称）
- **合并术语**：Y 条（同一术语多来源合并）
- **术语库当前总量**：总术语数 / 覆盖论文数

格式示例：
```
## 写作技法库入库（2026-07-16）

| 指标 | 数值 |
|------|------|
| 分析论文数 | 7 |
| 跳过论文数 | 82（模板化应用短文） |
| 新增技法 | 12 条 |
| 合并技法 | 0 条（首次入库） |

### 新增明细
- §1 摘要与引言：6 条（Abstract-001~003, Intro-001~003）
- §2 方法与数据：2 条（Method-001~002）
- §3 结果呈现：2 条（Result-001~002）
- §7 过渡衔接：2 条（Trans-001~002）

### 未覆盖类别
- §4 讨论论证：本批论文讨论部分发育不足
- §5 图表描述：日报卡片未捕获图表细节
- §6 引用整合：待积累

技法库当前：12 条 / 7 篇
```

不要假装全文解析成功；如果 PDF_TEXT_FULL 为 0，就明确说明没有达到入库证据标准。
```

---

## 常用命令速查

```powershell
python "D:\ruanjian\123\academic-workflow\01_读_论文阅读与复盘\00_core_scripts\process_desktop_pdfs_20260623.py" --help
python "D:\ruanjian\123\academic-workflow\01_读_论文阅读与复盘\00_core_scripts\backfill_daily_paper_cards.py" --help
python "D:\ruanjian\123\academic-workflow\01_读_论文阅读与复盘\00_core_scripts\finalize_daily_reading_batch.py" --help
```

## 相关文件

- 共享常量 → `00_core_scripts/_shared_constants.py`（BANNED_EXPRESSIONS、METHOD_KEYWORDS等）
- 桌面PDF全量处理 → `00_core_scripts/process_desktop_pdfs_20260623.py`
- 知识卡片补齐 → `00_core_scripts/backfill_daily_paper_cards.py`
- 每日批次安全收尾 → `00_core_scripts/finalize_daily_reading_batch.py`（写作技法批次登记 + 六项产物核验 + 仅删除已验证备份）
- PDF提取模块 → `pdf_ingest/`（7引擎级联）
- 论文阅读分级提示词 → `05_阅读提示词/01_daily_paper_reading.md`
- 知识卡片生成提示词 → `05_阅读提示词/02_knowledge_card_generation.md`
- 防伪精读保险提示词 → `05_阅读提示词/00_临时保险提示词_防伪精读.md`
