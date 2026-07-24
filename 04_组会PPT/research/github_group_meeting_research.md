# 组会系统 GitHub 调研与整合报告

> 调研时间：2026-06-04
> 调研者：Claude（组会工作流 + GitHub 开源调研 + Skill 整合助手）
> 组会路径：`<LOCAL_PATH>`

---

## 1. 总结论

| 问题 | 结论 |
|------|------|
| 是否需要直接整合 GitHub 项目 | **否** — 现有 ppt-speech-writer + academic-workflow 已满足核心需求 |
| 是否需要更新 ppt-speech-writer Skill | **是（最小更新）** — 建议新增 group_meeting_mode 说明 |
| 是否需要新增 rules/templates/checklists | **已完成** — 4 rules + 5 templates + 4 checklists 已创建 |
| 是否需要和 academic-workflow 打通 | **是** — 建议新增 weekly_group_meeting_digest 作为桥接 |
| 当前最小下一步 | 让 Codex 更新 SKILL.md 增加组会模式说明；等待用户准备好第一次组会时按模板执行 |
| 是否需要引入新依赖 | **否** — 零新依赖即可完成全部组会工作流 |

---

## 2. 已写入的组会核心规则

| 文件 | 内容 |
|------|------|
| `组会/CLAUDE.md` | 组会认知规则总入口：3 个目的、4 个误区、PPT 规则、工作流、目录结构 |
| `rules/meeting_mindset.md` | 核心心法：暴露问题 > 展示成果；每次组会前自问 4 个问题 |
| `rules/ppt_rules.md` | 10–15 页结构、每页 ≤7 行、每行 ≤20 字、禁止纯文字页 |
| `rules/advisor_expectations.md` | 导师最想听的 5 个问题、不希望看到的 5 种行为 |
| `rules/common_mistakes.md` | 5 个高频错误 + 3 个隐蔽错误，每个有症状/后果/修复 |
| `templates/weekly_group_meeting_outline.md` | Markdown 大纲模板：背景/进展/问题/前沿/计划/讨论 |
| `templates/ppt_10_15_pages_structure.md` | 12 页基准结构，每页一句话说明 |
| `templates/advisor_email_24h_before.md` | 组会前 24 小时邮件模板（含摘要 + 讨论问题） |
| `templates/paper_to_group_meeting.md` | 论文 → 组会材料转换模板（前沿动态 3 条 + 可迁移方法 2 条） |
| `templates/discussion_questions.md` | 组会讨论问题模板（方向/方法/资源/进展 4 类问题参考） |
| `checklists/before_meeting_checklist.md` | 提前 48h / 24h / 30min 三阶段检查清单 |
| `checklists/ppt_quality_checklist.md` | 全局 + 逐页 + 内容 + 视觉 4 维度 PPT 质量检查 |
| `checklists/speech_notes_checklist.md` | 讲稿检查：全局/逐页/开场/结尾 |
| `checklists/after_meeting_review.md` | 会后复盘：导师反馈/同伴收获/自我评估/下周行动/长期跟踪 |

---

## 3. GitHub 调研结果总表

| 类别 | 项目 | Stars | License | 最近更新 | 结论 |
|------|------|-------|---------|---------|------|
| **讲稿生成** | [AI272/speaker](https://github.com/AI272/speaker) | — | — | — | **A 类（已整合）** — 即 ppt-speech-writer Skill |
| **论文转 PPT** | [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides) | 3,274 | MIT | 活跃 | **B 类** — 可参考 RAG 抽取 + PPTX 生成流程 |
| **论文转 PPT** | [takashiishida/paper2slides](https://github.com/takashiishida/paper2slides) | — | 未明确 | 活跃 | **B 类** — 可参考 arXiv 直读 → Beamer 工作流 |
| **论文转 PPT** | [Auto-Slides](https://github.com/Westlake-AGI-Lab/Auto-Slides) | 497 | MIT | — | **B 类** — 可参考多 Agent 框架设计 |
| **PPT Lint** | [markusz/intern](https://github.com/markusz/intern) | — | — | — | **C 类** — Rust 二进制，定位不同，暂不使用 |
| **Slide Lint** | [nibzard/slidegauge](https://github.com/nibzard/slidegauge) | — | — | — | **B 类** — 可参考 Python 单文件 slide scoring 设计 |
| **PPTX 库** | [scanny/python-pptx](https://github.com/scanny/python-pptx) | — | MIT | 活跃 | **A 类（已整合）** — ppt-speech-writer 已使用 |
| **Marp 主题** | [kaisugi/marp-theme-academic](https://github.com/kaisugi/marp-theme-academic) | — | — | — | **C 类** — 当前坚持 PPTX，不转 Marp |
| **Quarto 模板** | [vitay/quarto-presentation](https://github.com/vitay/quarto-presentation) | — | — | — | **C 类** — 需 Quarto/R 环境，太重 |
| **习惯追踪** | [opethef10/habit_tracker](https://github.com/opethef10/habit_tracker) | ~10 | 未明确 | — | **不相关**（echo-life 项目属于不同域） |
| **热量计算** | [python-simple-tdee](https://github.com/gothburz/python-simple-tdee) | 2 | MIT | — | **不相关**（echo-life 健康模块） |

---

## 4. 可直接整合项目（A 类）

| 项目 | 可整合内容 | 目标文件夹 | 是否执行 |
|------|----------|----------|---------|
| AI272/speaker | **已整合** — 即 ppt-speech-writer Skill，包含全部 6 个脚本 | `组会/speaker/ppt-speech-writer/` | 已完成 |
| python-pptx | **已使用** — ppt-speech-writer 的核心依赖 | — | 已完成 |

---

## 5. 只参考设计项目（B 类）

| 项目 | 参考点 | 不直接整合原因 |
|------|--------|-------------|
| **HKUDS/Paper2Slides** (3,274⭐ MIT) | RAG 论文内容抽取 → PPTX 生成流程；可参考其"按章节拆分 → 每章生成 N 页幻灯片"的设计 | 依赖 OpenAI API + 复杂 RAG pipeline + 向量数据库，远大于组会需求；组会已有 academic-workflow 做论文理解 |
| **Auto-Slides** (497⭐ MIT) | 多 Agent 框架（Extraction → Planning → Verification → Repair）；可参考"一页一个核心观点检测"的 lint 设计 | LaTeX Beamer 输出，不匹配 PPTX 工作流 |
| **slidegauge** | 单文件 Python slide scorer 设计；可参考其逐页检查逻辑（length/bullets/lines/contrast） | Marp Markdown 格式，不匹配 PPTX |
| **takashiishida/paper2slides** | arXiv 源码 TeX 直读 → 展平 → LLM 生成 Beamer | License 未明确；生成的是 Beamer 不是 PPTX |

---

## 6. 暂不使用（C 类）

| 项目 | 原因 |
|------|------|
| **markusz/intern** (Rust) | Rust 二进制，需单独安装；功能与 ppt_quality_checklist.md 重叠（checklist 更灵活、可直接用 AI 执行） |
| **marp-theme-academic** | 当前坚持 PPTX 作为组会格式（导师和同学都用 PowerPoint），不引入 Markdown→slides 工具链 |
| **Quarto + Reveal.js 模板** | 需要 R/Quarto 环境，对于只用 Python + PPTX 的工作流过重 |
| **pptGEN-dev** (AGPLv3) | 语音→幻灯片生成（反向）；AGPLv3 License 风险 |

---

## 7. 禁止整合（D 类）

| 项目 | 原因 |
|------|------|
| 无 License 的论文转 PPT 工具 | 不能复制代码 |
| GPL/AGPL 项目 | 传染性 License，与 MIT 生态不兼容 |
| 商业闭源 PPT 生成服务 | 本地隐私优先，不上传 PPT 到第三方 |

---

## 8. ppt-speech-writer Skill 审查

### 当前适合做什么

| 能力 | 状态 | 组会适用性 |
|------|------|----------|
| 读取 PPTX 文本/表格/图表/SmartArt | ✅ 完善 | 直接可用 |
| 渲染幻灯片截图 + 视觉审查 | ✅ 完善 | 直接可用 |
| OCR 识别图片中的文字 | ✅ 完善 | 直接可用 |
| 双语演讲备注生成 | ✅ 完善 | 直接可用 |
| 注入干净 notes 到 PPTX | ✅ 完善 | 直接可用 |
| 生成展示版 DOCX 讲稿 | ✅ 完善 | 直接可用 |
| 视觉元素清点 + 覆盖率检查 | ✅ 完善 | 直接可用 |

### 当前缺什么（针对组会场景）

| 缺失能力 | 影响 | 建议 |
|---------|------|------|
| **组会模式** — 无专门的 group_meeting_mode 触发/配置 | 用户需要手动告诉 AI"这是组会用" | 在 SKILL.md 增加 group_meeting_mode 章节 |
| **导师追问问题生成** — 无"导师可能问什么"的输 出 | 汇报准备不充分 | 在 group_meeting_mode 输出中增加一项 |
| **讨论问题提取** — 不从 PPT 中自动识别"需要讨论的点" | 组会最后一页容易遗漏 | 可参考 ppt_quality_checklist 的检查项 |
| **会后复盘清单** — 无会后结构化输出 | 组会反馈容易忘记 | 已有 after_meeting_review.md 模板，无需改 Skill |
| **会前邮件草稿** — 无自动生成功能 | 需要手动写邮件 | 已有 advisor_email_24h_before.md 模板，无需改 Skill |

### 是否建议新增 group_meeting_mode

**建议新增，但做最小补充。** 不要破坏原有 speaker 功能。

建议在 SKILL.md 末尾增加：

```markdown
## Group Meeting Mode

When the user indicates this is for a group meeting / lab meeting / 组会:

1. After Deck Comprehension Brief (§7), add a "Questions The Advisor May Ask" section:
   - For each slide, predict 1–2 likely advisor questions
   - Focus on: methodology gaps, comparison to baselines, practical significance

2. In the display document (§12), add a "Discussion Points" section before the timing table:
   - Extract 2–3 specific questions the presenter wants to ask
   - Format each as: question + context (why this matters)

3. In the timing table (§12), mark a dedicated "Discussion" time block after the last content slide.

4. Remind the user to send materials 24 hours before the meeting (see 组会/checklists/).
```

### 是否需要新增脚本

**否。** 现有 6 个脚本（read_slides / render_slides / visual_inventory / vision_review / write_display_docx / inject_notes）已覆盖全部技术需求。组会模式只是对现有输出的组织和标注方式，不需要新脚本。

### 是否需要更新 SKILL.md

**是，做最小更新。** 在 SKILL.md 末尾增加上述 group_meeting_mode 段落。不修改现有 15 步工作流。

---

## 9. academic-workflow 整合建议

### 可以复用哪些内容

| academic-workflow 资产 | 组会可复用的内容 |
|----------------------|---------------|
| `reports/daily/` 每日论文日报 | 提取本周论文摘要（标题 + 一句话贡献） |
| `长期知识库.md` | 提取本周新增的知识卡片 |
| `paper_sources/` 论文源文件 | 提取本周下载的论文列表 |
| `prompts/` 提示词库 | 复用论文阅读和知识卡片的 prompt 风格 |

### 是否需要新增 weekly_group_meeting_digest

**建议新增。** 这是一个轻量脚本或手动模板，从 academic-workflow 本周产出中提取：

```
本周看了什么论文（3–5 篇）
↓
学到了什么方法（2 条可迁移）
↓
哪些没看懂（需要导师解释）
↓
哪些可以迁移到 GIS/遥感/空间分析
↓
下周准备验证什么
```

**实现方式**：
- **最小版**：手动用 `paper_to_group_meeting.md` 模板填写（当前阶段推荐）
- **自动化版（后续）**：写一个 Python 脚本读取 `reports/daily/` 和 `长期知识库.md`，自动生成 digest

### 是否需要 Codex 修改 academic-workflow

**当前不需要。** academic-workflow 是独立运转的系统，不因组会系统而修改。组会只是 academic-workflow 的一个下游消费方。

### 不建议做什么

- 不要在 academic-workflow 里内嵌组会逻辑
- 不要修改 `daily_paper_curator.py` 来适配组会
- 不要让组会系统反向驱动论文阅读节奏
- 不要为了"自动化"引入复杂调度依赖

---

## 10. 建议新增文件（总览）

| 文件 | 作用 | 是否已创建 |
|------|------|----------|
| `组会/CLAUDE.md` | 组会认知规则总入口 | ✅ 已更新 |
| `rules/meeting_mindset.md` | 心态与定位 | ✅ 已创建 |
| `rules/ppt_rules.md` | PPT 制作规则 | ✅ 已创建 |
| `rules/advisor_expectations.md` | 导师期望 | ✅ 已创建 |
| `rules/common_mistakes.md` | 常见错误 | ✅ 已创建 |
| `templates/weekly_group_meeting_outline.md` | 周组会大纲 | ✅ 已创建 |
| `templates/ppt_10_15_pages_structure.md` | PPT 结构模板 | ✅ 已创建 |
| `templates/advisor_email_24h_before.md` | 导师会前邮件 | ✅ 已创建 |
| `templates/paper_to_group_meeting.md` | 论文→组会材料 | ✅ 已创建 |
| `templates/discussion_questions.md` | 讨论问题模板 | ✅ 已创建 |
| `checklists/before_meeting_checklist.md` | 会前检查清单 | ✅ 已创建 |
| `checklists/ppt_quality_checklist.md` | PPT 质量检查 | ✅ 已创建 |
| `checklists/speech_notes_checklist.md` | 讲稿检查 | ✅ 已创建 |
| `checklists/after_meeting_review.md` | 会后复盘 | ✅ 已创建 |
| `research/github_group_meeting_research.md` | 本报告存档 | 待执行（复制此报告） |

---

## 11. Codex 接手报告（最小执行版）

### 当前任务

1. 更新 `组会/speaker/ppt-speech-writer/SKILL.md` — 新增 group_meeting_mode 段落
2. 将本调研报告复制到 `组会/research/` 存档

### 建议修改文件

| 文件 | 改动 | 风险 |
|------|------|------|
| `组会/speaker/ppt-speech-writer/SKILL.md` | 末尾新增 Group Meeting Mode 段落（约 20 行） | 极低 — 纯追加，不修改现有内容 |
| `组会/research/github_group_meeting_research.md` | 新建文件（复制本报告） | 无 |

### 必须遵守

- 不删除 speaker 原功能
- 不复制无 License 代码
- 不引入大型依赖
- 不把组会变成进度审判
- 不加入羞辱/惩罚式文案
- 组会定位为"获得指导"和"资源交换"

### 验收标准

- [x] 组会规则已写入 CLAUDE.md
- [x] PPT 结构规则已写入
- [x] 24 小时提前发送规则已写入
- [x] 导师最想听的 5 点已写入
- [x] 学生常犯 5 个错误已写入
- [ ] ppt-speech-writer SKILL.md 增加 group_meeting_mode 段落
- [x] academic-workflow 整合建议清楚
- [x] GitHub 调研有 License 判断
- [x] 没有直接复制高风险代码
- [x] 4 rules + 5 templates + 4 checklists 已创建

---

## 12. 最终判决

| 问题 | 答案 |
|------|------|
| 当前是否需要直接改 speaker skill | **是，最小更新** — 在 SKILL.md 末尾增加 group_meeting_mode 段落 |
| 当前是否需要新增组会模板 | **已完成** — 13 个文件已创建 |
| 当前是否需要让 Codex 接手 | **是，最小任务** — 更新 SKILL.md + 存档报告 |
| 当前是否需要继续调研 GitHub | **否** — 调研已覆盖全部 5 个方向，结论明确 |
| 哪些内容现在做，哪些以后做 | 见下方 |

### 现在做

- [x] 组会认知规则写入 CLAUDE.md
- [x] 4 个 rules 文件
- [x] 5 个 templates 文件
- [x] 4 个 checklists 文件
- [ ] 更新 ppt-speech-writer SKILL.md（group_meeting_mode）
- [ ] 存档调研报告到 `组会/research/`

### 以后做（等第一次实际组会前）

- [ ] 用 `paper_to_group_meeting.md` 模板填写第一次组会材料
- [ ] 用 `ppt_10_15_pages_structure.md` 做第一个组会 PPT
- [ ] 用 `/ppt-speech-writer` 生成讲稿
- [ ] 用 `before_meeting_checklist.md` 检查准备情况
- [ ] 组会后用 `after_meeting_review.md` 复盘
- [ ] 如果需要自动化 weekly digest → 设计脚本（但现在不做）

### 最终原则

组会系统的目标不是做一个漂亮文件夹，而是让每次组会都能更清楚地向导师暴露问题、获得指导、整理前沿动态、学习同伴方法。

---

*报告由 Claude 完成。所有文件已写入 `<LOCAL_PATH>`。*
