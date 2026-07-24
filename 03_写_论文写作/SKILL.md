# 03 写_论文写作 — 指针文件

> **2026-07-13 合并**: 本目录原 `SKILL.md` (cn-core-paper) 已合并入 `.claude/skills/academic-paper-writing/SKILL.md`。
> 写作任务统一由 `academic-paper-writing` skill 接管。

## 实际入口

**Skill**: `/academic-paper-writing`（`<LOCAL_PATH>`）

## 本目录结构

```
03_写_论文写作/
├── SKILL.md                    ← 本文件（指针）
├── README.md / README_速查.md
├── prompts/                    ← 16个写作Prompt（由 skill 路由加载）
├── references/                 ← 中文核心论文参考文件（由 skill 按需加载）
├── AI整篇论文写作工作流/        ← 整篇生成工作流（由 skill §5 加载）
├── checklists/                 ← 4个检查清单（由 skill 引用）
├── 02_写作模板/                 ← 3个写作模板（由 skill 引用）
├── 01_投稿准备/                 ← 2026-07-13新增：期刊匹配/投稿信/终稿检查
├── 02_审稿应对/                 ← 2026-07-13新增：审稿意见拆解/回复/补充实验/大修
├── 03_学术传播/                 ← 2026-07-13新增：答辩预演/学术海报
├── skills/                     ← DEPRECATED：孤儿子skill已删除，见 DEPRECATED.md
├── 00_core_scripts/            ← 9个写作辅助脚本
├── 03_段落素材/                 ← 测试素材和语法报告
└── config/ / tests/ / github_research/
```

## 已合并的独有内容

原 cn-core-paper 本地 SKILL.md 的以下独有内容已注入 skill 版：
- 三层优先级（先主线→再数据→再语言→再润色）
- 一句话默认策略（主线→数据→语言→图表公式→总检）
- 6类任务分类和对应参考文件映射
