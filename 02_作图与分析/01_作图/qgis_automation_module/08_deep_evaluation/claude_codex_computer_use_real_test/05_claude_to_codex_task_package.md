# 05 Claude → Codex 作图任务包

---

【执行身份】
你是 Codex。你必须使用 Computer Use 控制 Windows 上的 QGIS 执行作图。Claude 只提供任务指令，不直接作图。

【当前状态】
- Codex 额度状态：等待 Codex 会话确认
- Computer Use 状态：等待 Codex 初始化
- QGIS 状态：<LOCAL_PATH> v4.0.2

【任务目标】
使用 Natural Earth 公开数据制作"中国及周边主要城市专题图"，生成操作前/后/对比图。

【输入数据】
| 文件路径 | 类型 | 说明 |
|---------|------|------|
| Natural Earth Admin 0 Countries (1:110m) | 矢量面 | 177国边界 |
| Natural Earth Populated Places (1:110m) | 矢量点 | 243城市 |

下载地址：
- https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip
- https://naciscdn.org/naturalearth/110m/cultural/ne_110m_populated_places_simple.zip

【输出要求】
输出到：`claude_codex_computer_use_real_test\after_outputs\20260606_natural_earth_china_cities\`

1. before_preview.png
2. after_map.png
3. after_map.pdf
4. after_project.qgz
5. before_after_comparison.png
6. codex_qgis_execution_log.md

【地图元素】
- 标题：Natural Earth 中国及周边主要城市专题图
- 图层顺序：国家面→城市点
- 坐标系：EPSG:4326
- 范围：中国及周边 (lon 68-150, lat 5-55)
- 样式：中国红色突出，其他国家浅灰；城市按 scalerank 分级着色
- 标注：主要城市 NAME 字段
- 图例：是
- 比例尺：是
- 指北针：是
- 导出 DPI：300

【必须读取的本地依据】
1. qgis_common_tasks.md (25项)
2. qgis_vector_workflow.md
3. qgis_layout_export_manual.md
4. qgis_cartography_style_guide.md
5. qgis_error_recovery.md
6. 03_pyqgis_templates/
7. computer_use_qgis_steps.md
位置：`qgis_automation_module/`

【操作步骤】
1. 初始化 Computer Use → 2. 打开 QGIS → 3. 确认版本 → 4. 下载数据 → 5. 解压 → 6. 加载图层 → 7. 导出 before → 8. 筛选中国区域 → 9. 应用样式 → 10. 创建布局 → 11. 添加地图元素 → 12. 导出 after → 13. 保存项目 → 14. 生成对比图 → 15. 生成日志

【验收标准】
- [x] 共15项（见 before/after/comparison/validation）

【硬性停止条件】
1. Computer Use 不可用 → 停止
2. QGIS 不可启动 → 停止
3. 数据下载失败 → 停止
4. 输出路径会覆盖已有成果 → 停止
