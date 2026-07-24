# QGIS Automation Module — QGIS 自动作图操作模块

> 位置: `02_作图与分析/01_作图/qgis_automation_module/`
> 目标: Claude 拆解任务 → Codex 执行 QGIS 操作 → 产出地图/分析结果
> Codex 额度耗尽时：暂停作图，等待额度恢复

---

## 模块结构

```
qgis_automation_module/
├── README.md                          ← 本文件
├── 00_research/                       ← 调研资料 (GitHub top300, 评分, 深度笔记)
├── 01_local_skills/                   ← 本地 QGIS 技能索引与适配
├── 02_operation_manuals/              ← QGIS 操作手册 (Claude指令 + Codex步骤 + PyQGIS)
├── 03_pyqgis_templates/               ← 可复用 PyQGIS 脚本模板 (8+)
├── 04_claude_to_codex_protocol/       ← Claude→Codex 工作协议
├── 05_plugin_and_repo_library/        ← 推荐插件/仓库/风险清单
├── 06_examples/                       ← 4个完整示例 (基础制图/矢量分析/栅格专题/批量导出)
├── 07_validation/                     ← 验证清单
└── 99_archive/                        ← 归档 (repo快照等)
```

---

## 当前 Claude → Codex 连接方式

不使用 Claude 直接调用 Codex。使用任务包交接：

```
Claude 生成任务包 → task_queue/
  → 用户打开 Codex 会话
  → Codex 读取任务包
  → Codex 使用 Computer Use 操作 QGIS
  → 结果输出到 task_results/
  → Claude 验收
```

**禁止：** Claude 本地作图 | 用户手动替代 | PyQGIS 粘贴 | qgis_process | 安装桥接工具 | 输入 token

## 当前 Computer Use 状态

当前 QGIS 真实作图测试受阻于：

Computer Use native pipe path is unavailable

因此：

* 当前不执行作图。
* 当前不使用 Claude 本地作图替代。
* 当前不使用普通 Python 作图替代。
* 当前不要求用户手动替代。
* 已生成任务包，等待 Codex Computer Use 恢复。

## 使用方式

### 正常流程 (有 Codex 额度)

1. **Claude** 接收用户作图需求
2. **Claude** 查阅 `02_operation_manuals/` 找到对应操作手册
3. **Claude** 使用 `04_claude_to_codex_protocol/claude_instruction_template.md` 生成指令
4. **Codex** 使用 computer use 打开 QGIS，按 `computer_use_qgis_steps.md` 执行
5. **Codex** 如需 PyQGIS 脚本，使用 `03_pyqgis_templates/` 中的模板
6. **Codex** 导出地图，截图确认，回传结果

### QGIS 作图执行规则

1. **Codex 是唯一 QGIS 作图执行者。** Claude 不直接运行 QGIS、不直接生成地图。
2. **Codex 必须使用 computer use 插件。**
3. **Codex 必须使用本模块中的：** 操作手册、PyQGIS 模板、Claude→Codex 协议、验证清单。
4. **Codex 不可用 → 暂停。** Codex 额度耗尽 → 暂停。QGIS 不可用 → 暂停 QGIS 作图。
5. **不启用 Claude 直接作图。** 不启用用户手动替代。不启用 PyQGIS 粘贴。不启用 qgis_process。
6. **没有 Codex 执行日志 + 输出文件 → 不算作图完成。**
7. Codex 不可用时，Claude 只生成待执行任务包（`codex_waiting_task_package_template.md`）。

详见 `04_claude_to_codex_protocol/quota_exhausted_fallback.md`

---

## 核心原则

- 不删除原始数据
- 不覆盖已有成果
- 不安装未验证插件
- 不修改系统 QGIS 配置
- 优先使用本地模板和操作手册
- 所有路径使用占位符，不写死用户路径
