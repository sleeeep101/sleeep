# Project Integration Matrix

> 基于 GitHub 200+ 项目调研生成的完整项目整合矩阵
> 生成方式: write_integration_core.py 自动生成

## 字段说明

| 字段 | 含义 |
|------|------|
| rank | 按 stars 排名 |
| repo | 仓库名 |
| stars | Star 数 |
| capability_tags | 能力标签 |
| integration_action | 整合方式 |
| license_risk | License 风险 |
| complexity_risk | 复杂度风险 |

## integration_action 说明

| 动作 | 含义 |
|------|------|
| direct_script_wrapper | 直接薄脚本包装（Apache/MIT/BSD 轻量工具） |
| prompt_template | 提取为 Prompt 模板（原创整合版） |
| skill_pattern | 吸收为 Skill 设计模式 |
| checklist_rule | 吸收为检查清单规则 |
| format_template_reference | 格式/模板参考（不直接依赖） |
| resource_index_only | 仅作为资源索引记录 |
| watch_later | 暂缓观察 |
| reject | 不接入（License/学术诚信/过重） |

## 统计

- 总项目数: 146 (来自CSV) + 补充
- 直接脚本包装: 见 project_integration_matrix.csv
- Prompt 模板: 见 project_integration_matrix.csv
- Skill 模式: 见 project_integration_matrix.csv
- 检查清单规则: 见 project_integration_matrix.csv
- 仅资源索引: 见 project_integration_matrix.csv
- 暂缓观察: 见 project_integration_matrix.csv
- 拒绝接入: 见 project_integration_matrix.csv

详细数据见 `project_integration_matrix.csv`
