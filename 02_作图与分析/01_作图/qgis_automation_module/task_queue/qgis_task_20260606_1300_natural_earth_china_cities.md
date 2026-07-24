# QGIS 作图任务包：Natural Earth 中国及周边主要城市专题图

> 当前状态：等待 Codex Computer Use 恢复。
> 最近失败原因：Computer Use native pipe path is unavailable。
> 当前不得标记为完成。
> 等 Computer Use 恢复后，由 Codex 读取本任务包继续执行。

> **当前文件是 Claude 生成的待执行任务包，不是作图成果。**
> 只有 Codex 使用 Computer Use 实际打开 QGIS 并生成输出文件后，任务才算完成。

---

## 1. 执行身份

你是 Codex。你必须使用 Computer Use 控制 Windows 上的 QGIS 执行作图。Claude 只负责生成任务包，不直接作图。用户不承担手动替代执行。

## 2. 硬性停止条件

出现任一情况，立即停止实际作图：
- Codex 额度耗尽
- 当前 Codex 会话没有 Computer Use
- Computer Use 初始化失败
- 出现 `Computer Use native pipe path is unavailable`
- QGIS 不可启动（<LOCAL_PATH> v4.0.2）
- 输入数据下载失败
- 输出路径会覆盖已有成果

停止后只写失败原因，不得写作图完成。

## 3. 本地依据

执行前必须读取以下文件（位于 `qgis_automation_module/`）：
- `02_operation_manuals/qgis_common_tasks.md`
- `02_operation_manuals/qgis_vector_workflow.md`
- `02_operation_manuals/qgis_layout_export_manual.md`
- `02_operation_manuals/qgis_cartography_style_guide.md`
- `02_operation_manuals/qgis_error_recovery.md`
- `04_claude_to_codex_protocol/task_package_handoff_standard.md`
- `03_pyqgis_templates/`

## 4. 任务目标

使用 Natural Earth 公开数据制作"中国及周边主要城市专题图"，生成操作前/后/对比图。

## 5. 数据来源

Natural Earth 1:110m 公开数据 (Public Domain)：
- Admin 0 Countries: `https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip`
- Populated Places: `https://naciscdn.org/naturalearth/110m/cultural/ne_110m_populated_places_simple.zip`

下载到：`task_results/natural_earth_china_cities_20260606/input_raw/`
记录：下载 URL、文件大小、SHA256、解压路径、数据许可。

## 6. 输出目录

所有成果输出到：`task_results/natural_earth_china_cities_20260606/`

必须生成：
1. before_preview.png
2. after_map.png
3. after_map.pdf
4. after_project.qgz
5. before_after_comparison.png
6. codex_qgis_execution_log.md
7. validation_result.md

## 7. 操作前图

加载 countries + populated places 原始图层 → 不筛选 → 默认样式 → 全球视图 → 导出 before_preview.png。禁止用 after_map 或无关图片冒充。

## 8. 处理链

1. 筛选 SOVEREIGNT IN (China, Japan, South Korea, North Korea, Mongolia, Russia, Kazakhstan, Kyrgyzstan, Tajikistan, Pakistan, Afghanistan, Nepal, Bhutan, Myanmar, Laos, Vietnam, Thailand, Cambodia, Bangladesh, Taiwan, Philippines, India)
2. 中国选区红色填充+粗轮廓，其他国家浅灰
3. 城市按 scalerank 分级着色（红→橙→蓝→绿，大小递减）
4. 地图范围：中国及周边
5. 创建 Print Layout → 添加标题/图例/比例尺/指北针 → 导出 PNG(300dpi)+PDF → 保存 QGZ
6. 生成 before_after_comparison.png（左=before，右=after）

## 9. 地图元素

- 标题：Natural Earth: China & Surrounding Major Cities
- 图层顺序：国家面 → 城市点
- 坐标系：EPSG:4326
- 配色：中国红色突出，其他国家浅灰，城市分级着色

## 10. 执行日志

生成 codex_qgis_execution_log.md，记录每一步的输入/输出/成功/失败/处理方式。

## 11. 验收标准

- [ ] Computer Use 实际参与
- [ ] QGIS 成功打开（v4.0.2）
- [ ] Natural Earth 数据实际下载
- [ ] before_preview.png 存在
- [ ] after_map.png 存在
- [ ] after_map.pdf 存在
- [ ] after_project.qgz 存在
- [ ] before_after_comparison.png 存在
- [ ] before 和 after 同源且有明显处理关系
- [ ] 原始数据未被覆盖
- [ ] 有 Codex 执行日志
- [ ] 没有手动替代/伪图/未知插件

## 12. 完成判定

只有当以上所有文件同时存在，才能写作图完成。否则写"未完成"并说明原因。
