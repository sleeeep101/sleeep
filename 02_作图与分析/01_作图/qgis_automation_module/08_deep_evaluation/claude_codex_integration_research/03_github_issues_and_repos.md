# 03 GitHub 调研记录

| 来源 | 类型 | 标题 | 链接 | 相关性 | 发现 | 可用 | 风险 |
|------|------|------|------|:---:|------|:---:|------|
| OpenAI 官方 | 仓库 | openai/codex-plugin-cc | github.com/openai/codex-plugin-cc | ★★★★★ | **官方 Claude Code 插件，让 Codex 运行在 Claude Code 内部** | ✅ | 低 (Apache 2.0) |
| npm | 包 | subcodex-mcp | npmjs.com/package/subcodex-mcp | ★★★★ | Codex 作为 Claude Code 子 agent，含 stall detection | ✅ | 中 (社区维护) |
| npm | 包 | claude-codex-bridge | npmjs.com/package/claude-codex-bridge | ★★★★ | 双向 MCP 桥接 | ✅ | 中 (社区) |
| pypi | 包 | crossby | pypi.org/project/crossby | ★★★ | 跨工具会话 handoff (--from claude --to codex) | ✅ | 低 |
| npm | 包 | all-agents-mcp | — | ★★★ | 多 agent CLI 调用 | ⚠️ | 中 |
| GitHub | issue | LINUX DO 多个线程 | linux.do | ★★★ | Computer Use 在 Windows Codex 上的已知问题 | 参考 | 低 |
| CSDN | 博客 | 解决windows上codex不能跑本地应用 | blog.csdn.net | ★★ | Windows Codex Computer Use 修复方法 | 参考 | 低 |

## 关键发现

### 官方方案：codex-plugin-cc (2026-03-30)

OpenAI 发布了官方 Apache 2.0 插件，提供 slash commands：
- `/codex:review` — 代码审查
- `/codex:rescue` — 交任务给 Codex 子 agent（支持后台）
- `/codex:status` `/codex:result` `/codex:cancel` — 任务管理

**前提条件：**
- Node.js 18.18+
- ChatGPT 订阅 或 OpenAI API key
- Codex Desktop app 本地运行

### Computer Use native pipe path 问题

多个 LINUX DO 线程确认这是 Codex Windows Desktop 版本的已知问题：
- 版本 26.519 中 Computer Use 插件短暂出现后消失
- 与 Windows 原生 pipe/Named Pipe 权限、沙箱、native host 初始化有关
- macOS 上有修复指南，Windows 上仍不稳定
