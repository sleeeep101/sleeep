# nature-skills 整合说明

> 整合日期：2026-07-14
> 源仓库：https://github.com/Yuan1z0825/nature-skills
> 本地路径：`<LOCAL_PATH>`

## 整合策略

nature-skills 作为**补充技能库**接入 academic-workflow，不替代现有技能。采用"稳定克隆 + Agent wrapper + 规则提取"三层架构：

| 层级 | 方式 | 用途 |
|------|------|------|
| **Agent wrapper** | `<LOCAL_PATH>` | Claude Code 可直接调用的 subagent，指向本地 clone 的 SKILL.md |
| **规则提取** | `references/nature-skills/*.md` | 从 nature-skills 提取的关键规则，融入 academic-workflow 流程 |
| **本地 clone** | `<LOCAL_PATH>` | `git pull` 即可更新，Agent wrapper 自动指向最新版本 |

## 已采用的 nature-skills 内容

| Skill | 状态 | 采用方式 | 用途 |
|-------|------|----------|------|
| `nature-reader` v2.0 | Beta | Agent wrapper + 规则参考 | 中英文对照论文精读，补充 pdf-image-text-extractor 不具备的双语对照/图表定位功能 |
| `nature-polishing` v6.1.0 | Stable | Agent wrapper | 学术英文润色/中译英，补充 academic-paper-writing 偏重中文写作的定位 |
| `nature-statistics` | Draft | Agent wrapper + 规则提取 | 统计报告审查，academic-workflow 此前无覆盖 |
| `nature-proposal-writer` v1.0.0 | Beta | Agent wrapper | Proposal-first 写作状态机，补充开题/基金申请场景 |
| `nature-literature-pipeline` v1.0.0 | Stable | 规则提取（6维评分） | 6维评分系统融入论文预筛，增强现有 A/B/C/X 分级 |
| `_shared/core/terminology-ledger.md` | — | 规则提取 | 术语一致性规则融入论文写作质量核验 |
| `_shared/core/paper-type-taxonomy.md` | — | 规则提取 | 论文类型分类（research/methods/hypothesis/algorithmic/review）融入阅读策略 |

## 未采用的内容及原因

| Skill | 原因 |
|-------|------|
| `nature-figure` v2.0 | 已有 `scientific-figure` skill 覆盖，功能重叠 |
| `nature-writing` v1.0.0 | 已有 `academic-paper-writing` skill 覆盖 |
| `nature-paper2ppt` | 已有 `group-meeting-ppt` skill 覆盖 |
| `nature-citation` | 用户不依赖 Nature/CNS 引用检索，当前 KB schema 已覆盖引用需求 |
| `nature-data` | 用户当前无需 Data Availability Statement 准备 |
| `nature-response` | 审稿回复已由 `academic-paper-writing` + Prompt #52-55 覆盖 |
| `nature-academic-search` | 在线检索已搁置（2026-07-13），且含 MCP 服务器等重依赖 |
| `nature-downloader` | 用户通过桌面 PDF 手动下载，流程不涉及图书馆/CARSI |
| `nature-experiment-log` | 用户无湿实验，不涉及实验日志记录 |
| `nature-paper-to-patent` | 不涉及专利转化 |
| `nature-reviewer` | Pre-submission review 可由 Prompt #59 覆盖 |
| `nature-ref-verifier` | 参考文献核验已由 Prompt #51 + 写作质量核验覆盖 |

## 后续使用

### 跨仓库精进（2026-07-24 新增）

除 Yuan1z0825/nature-skills 外，已完成以下三个仓库的方法论提取与融合：

| 源仓库 | 提取内容 | 详见 |
|--------|---------|------|
| Boom5426/Nature-Paper-Skills | 声明-证据映射、五层审计、图表声明规划、Results 架构速查、英文散文风格 | `cross-repo-insights.md` |
| bahayonghang/academic-writing-skills | LaTeX 编译诊断、GB/T 7714 审计、投稿前格式检查 | `cross-repo-insights.md` §十一 |
| SNL-UCSB/paper-writing-skill | Introduction-Twice、七种压缩操作、编辑原则、主题句先行 | `cross-repo-insights.md` §三/§六/§七/§八 |

**核心文件**：`<LOCAL_PATH>` — 写作任务时自动加载。

### Agent 调用

在 Claude Code 中直接使用 subagent：

```
Use the nature-reader subagent to read this paper.
```

```
Use the nature-polishing subagent to polish this paragraph into Nature-style English.
```

```
Use the nature-statistics subagent to audit the statistical analysis section.
```

```
Use the nature-proposal-writer subagent to draft a research proposal.
```

### 更新 nature-skills

```bash
cd <LOCAL_PATH> && git pull
```

Agent wrapper 自动指向最新版本，无需额外操作。

### 评分系统参考

论文预筛时参考 `references/nature-skills/scoring-system.md` 的 6 维评分逻辑，增强现有 A/B/C/X 分级。

### 术语一致性

论文写作后使用 `references/nature-skills/terminology-ledger.md` 的术语账本方法，确保中英文术语全文统一。
