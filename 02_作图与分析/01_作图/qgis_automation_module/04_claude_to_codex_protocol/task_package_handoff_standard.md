# Claude → Codex 任务包交接标准

## 1. 目的

Claude 无法直接调用 Codex。本文件规定 Claude 生成任务包、Codex 读取并执行的标准流程。

## 2. 标准流程

```
用户需求
  → Claude 生成 QGIS 作图任务包
  → 保存到 task_queue/
  → 用户在 Codex 可用环境中打开 Codex
  → Codex 读取任务包
  → Codex 使用 Computer Use 操作 QGIS
  → Codex 输出地图、日志、截图到 task_results/
  → Claude 读取结果并验收
```

## 3. 任务包路径

- 任务包: `qgis_automation_module/task_queue/qgis_task_YYYYMMDD_HHMM_taskname.md`
- 结果: `qgis_automation_module/task_results/YYYYMMDD_taskname/`

## 4. 完成判定

必须同时有:
- Codex 执行日志
- 输出地图 (PNG/PDF/QGZ)
- before/after 对比文件
- 输入输出关系可追溯

## 5. 不算完成

- 只有任务包无 Codex 执行
- 无输出文件
- 无执行日志
- 原始文件被修改

## 6. Codex 不可用时

- 暂停作图
- 任务包保留在 task_queue/
- 不提供替代执行方案
