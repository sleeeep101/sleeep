# 05 候选方案

| 方案 | 可行性 | 安全性 | 官方 | 适合QGIS GUI | 需token | 推荐度 | 结论 |
|------|:---:|:---:|:---:|:----------:|:-----:|:----:|------|
| A: 官方 codex-plugin-cc | ★★★★ | ★★★★★ | ✅ OpenAI | ✅ | ChatGPT订阅或API key | ⭐⭐⭐⭐⭐ | **首选** |
| B: 任务包交接 (已建成) | ★★★★★ | ★★★★★ | N/A | ✅ | 否 | ⭐⭐⭐⭐ | 已可用 |
| C: subcodex-mcp | ★★★ | ★★★ | ❌ | ✅ | 可能需要 | ⭐⭐⭐ | 备选 |
| D: crossby handoff | ★★★ | ★★★★ | ❌ | 间接 | 否 | ⭐⭐⭐ | 备选 |
| E: GitHub Actions/IssueOps | ★ | ★★★ | ✅ | ❌ | 否 | ⭐ | 不适合GUI |

## 方案 A: 官方 codex-plugin-cc (推荐)

- **来源**: openai/codex-plugin-cc, Apache 2.0, 2026-03-30
- **原理**: Claude Code 插件系统 + 本地 Codex Desktop JSON-RPC
- **命令**: `/codex:rescue` 把任务交给 Codex 子 agent
- **限制**: 需要 ChatGPT 订阅或 OpenAI API key + Node.js 18.18+

## 方案 B: 任务包交接 (当前可用)

- **原理**: Claude 生成 markdown 任务包 → Codex 阅读并执行 → Claude 验收结果
- **优势**: 零依赖、零 token、已建成
- **限制**: 需要用户手动在 Codex 会话中打开任务包

## 方案 C: subcodex-mcp

- **原理**: MCP 服务器让 Claude Code 把 Codex 作为子 agent 调用
- **优势**: 自动 stall detection 和恢复
- **风险**: npm 社区包，需审计

## 方案 F: 保持暂停

- **原理**: Codex 不可用时暂停，不强制替代
- **适用**: 当上述方案不可用时
