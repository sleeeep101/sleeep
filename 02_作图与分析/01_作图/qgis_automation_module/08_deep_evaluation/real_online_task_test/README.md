# 真实在线 QGIS 作图端到端测试

## 状态：暂停

| 前置条件 | 状态 |
|---------|:--:|
| Codex computer use 可用 | ❌ Claude 无法调用 Codex |
| QGIS 本机已安装 | ❌ 未找到 |
| qgis_automation_module 存在 | ✅ 12模板+6手册+4协议 |
| Natural Earth 可访问 | ✅ |
| 磁盘空间充足 | ✅ 182.5 GB |

## 决策

Codex 不可用 + QGIS 未安装 → **停止实际作图。**

不伪造输出。不提供用户手动替代方案。

## 已生成

- `01_data_source.md` — 数据来源清单
- `04_claude_to_codex_instruction.md` — Claude 给 Codex 的完整作图指令
- 以下条件满足时即可执行：
  1. 本机安装 QGIS (>=3.28)
  2. Codex computer use 可用
  3. 运行 04 指令即可开始测试
