# 01 环境检查

| 检查项 | 结果 | 详情 |
|--------|:--:|------|
| Computer Use 可用 | ❌ | Claude 工具列表中无 Computer Use：仅 Read/Write/Edit/Bash/PowerShell/Grep/Glob |
| QGIS 已安装 | ✅ | <LOCAL_PATH> v4.0.2 |
| qgis_automation_module | ✅ | 65 files |
| Natural Earth 可访问 | ✅ | naciscdn.org CDN |
| 输出目录写入权限 | ✅ | OK |

## 判定

Computer Use 不可用 → 停止实际作图。生成待执行任务包。不伪造输出。不提供用户手动替代方案。
