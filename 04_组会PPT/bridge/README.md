# Bridge — academic-workflow ↔ 组会系统桥接

> 把 daily paper reading 的结果变成组会可用的材料。
> bridge 只做规则和模板，不直接修改 academic-workflow。

## 数据流

```
academic-workflow/reports/daily/*.md    (每日论文日报)
academic-workflow/长期知识库.md          (累积知识库)
academic-workflow/paper_sources/*/       (论文源文件)
        ↓
    [手动 / 模板填写]
        ↓
组会/bridge/weekly_group_meeting_digest  (周组会摘要)
        ↓
组会/bridge/paper_reading_to_ppt_outline (PPT 大纲)
        ↓
    [ppt-speech-writer Skill]
        ↓
组会/outputs/speaker_notes/              (讲稿)
组会/outputs/advisor_email/              (会前邮件)
        ↓
    [组会]
        ↓
组会/outputs/after_meeting_review/       (会后复盘)
```

## 文件

| 文件 | 作用 |
|------|------|
| `weekly_group_meeting_digest_template.md` | 从论文日报生成周组会摘要 |
| `paper_reading_to_ppt_outline.md` | 从周摘要生成 10–15 页 PPT 大纲 |
| `simulated_meeting_plan_before_2026_09.md` | 9 月前的模拟演练计划 |
| `september_launch_checklist.md` | 9 月正式启动检查清单 |
| `README.md` | 本文件 |

## 原则

- 先手动用模板执行，确认流程合理 → 再考虑自动化脚本
- 不修改 academic-workflow 主流程
- 组会是 academic-workflow 的下游消费方，不反向控制论文阅读节奏
- 2026 年 9 月前所有产出标注"模拟组会材料"
