# QGIS Automation Module 验证清单

## GitHub 300 调研验证

- [ ] github_top300_qgis_repos.csv 存在 (~180项，GitHub API限制)
- [ ] github_top300_qgis_scorecard.csv 存在 (62项评分)
- [ ] selected_repos_deep_notes.md 覆盖 A类仓库 (20个)
- [ ] github_b_class_extracts.md 存在
- [ ] github_essence_to_local_mapping.md 存在
- [ ] 明确标注实际获取数量(~180)，未虚报300

## 模块结构验证

- [ ] `qgis_automation_module/` 目录存在
- [ ] `00_research/` 含 GitHub CSV + 本地审计
- [ ] `02_operation_manuals/` 含操作手册
- [ ] `03_pyqgis_templates/` 含 >=8 模板
- [ ] `04_claude_to_codex_protocol/` 含指令模板 + Computer Use + 额度耗尽暂停策略 + 待执行任务包模板
- [ ] `05_plugin_and_repo_library/` 含推荐插件 + 仓库 + 风险
- [ ] `06_examples/` 含 >=4 示例
- [ ] `07_validation/` 含验证清单
- [ ] `README.md` 存在

## PyQGIS 模板语法检查

- [ ] `load_vector_layer.py` 语法通过
- [ ] `load_raster_layer.py` 语法通过
- [ ] `apply_style_qml.py` 语法通过
- [ ] `create_layout_export_png_pdf.py` 语法通过
- [ ] `batch_export_maps.py` 语法通过
- [ ] `vector_clip_buffer_intersect.py` 语法通过
- [ ] `raster_clip_reproject.py` 语法通过
- [ ] `project_save_and_package.py` 语法通过

## Codex 额度耗尽策略验证

- [ ] `quota_exhausted_fallback.md` 为"暂停策略"，不包含 A-F 替代方案
- [ ] 未出现用户手动执行方案推荐
- [ ] 未出现 PyQGIS 粘贴执行方案推荐
- [ ] 未出现 qgis_process 替代方案推荐
- [ ] 未出现 GUI 手动点击替代方案推荐
- [ ] `codex_waiting_task_package_template.md` 存在
- [ ] 示例文件中无 "fallback / 替代方案" 推荐
- [ ] README 中无推荐额度耗尽时手动作图
- [ ] 全局搜索结果无残留旧方案

## 安全验证

- [ ] 无 token/cookie/API key
- [ ] 无对系统 QGIS 配置的修改
- [ ] 无超大数据集下载
- [ ] 无覆盖已有成果

## 功能验证 (需真实 QGIS 环境 + Codex 额度)

- [ ] 加载矢量图层成功
- [ ] 加载栅格图层成功
- [ ] Print Layout 导出 PNG 成功
- [ ] 矢量裁剪成功
- [ ] 栅格山影生成成功
- [ ] Claude 指令模板可被 Codex 理解执行

## 作图执行规则验证

- [ ] 是否由 Codex 实际执行（非 Claude 直接作图）
- [ ] 是否使用 computer use
- [ ] 是否使用本地作图技巧（操作手册/PyQGIS 模板）
- [ ] 是否有 Codex 执行日志
- [ ] 是否有输出文件（PNG/PDF/QGZ）
- [ ] 是否有截图或导出图
- [ ] 是否有输入→处理→输出关系说明
- [ ] 是否没有 Claude 直接作图
- [ ] 是否没有用户手动替代
- [ ] 是否没有 PyQGIS 手动粘贴
- [ ] 是否没有 qgis_process 替代
- [ ] Codex 不可用时是否暂停（不提供替代方案）
- [ ] 未执行任务是否没有被标记完成
