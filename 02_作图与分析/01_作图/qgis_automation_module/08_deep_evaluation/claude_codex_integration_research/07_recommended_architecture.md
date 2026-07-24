# 07 推荐架构

## 结论

**当前阶段不追求 Claude 直接调用 Codex。优先使用官方 codex-plugin-cc（如条件满足），否则使用任务包交接。**

## 推荐: 三级方案

### 一级（如 ChatGPT 订阅可用）：安装官方 codex-plugin-cc

```
Claude Code (含 codex-plugin-cc)
  → /codex:rescue → Codex 子 agent
  → Codex 使用 Computer Use 打开 QGIS
  → Codex 读取 qgis_automation_module
  → 执行作图 → 输出成果
```

**前提**: ChatGPT 订阅/OpenAI API key + Node.js 18.18+ + Codex Desktop

### 二级（当前可用）：任务包交接

```
Claude 生成任务包 (05_claude_to_codex_task_package.md)
  → 用户打开 Codex 会话
  → Codex 读取任务包
  → Codex 使用 Computer Use 操作 QGIS
  → Codex 输出成果和日志
  → Claude 读取成果验收
```

### 三级（备选）：subcodex-mcp 或 crossby

如一级不可用且二级不够自动化，可评估社区桥接工具。

## 不可用时的处理

- Codex Computer Use 不可用 → 暂停作图
- 不强制使用替代方案
- 不引入高风险桥接工具
