# 02 QGIS 操作覆盖矩阵

> 评分: 0=没有 1=泛泛说明 2=有说明不可执行 3=有步骤/模板 4=有模板+错误处理 5=真实任务验证

| # | 操作项 | 评分 | 覆盖文件 | 问题 | 最小修复 |
|---|--------|:---:|---------|------|---------|
| 1 | QGIS 启动与版本确认 | 3 | computer_use_qgis_steps.md §1 | GUI步骤清晰，缺少PyQGIS版本检测 | 加 QGIS version check 脚本 |
| 2 | 新建项目 | 3 | qgis_common_tasks.md §1 | 有PyQGIS+GUI步骤 | — |
| 3 | 打开已有项目 | 2 | qgis_common_tasks.md §1 | 有 project.write() 但缺 project.read() | 补充 load project 模板 |
| 4 | 加载矢量图层 | 4 | load_vector_layer.py + common_tasks §2 | 有完整错误处理 | — |
| 5 | 加载栅格图层 | 4 | load_raster_layer.py + common_tasks §3 | 有完整错误处理 | — |
| 6 | CRS / EPSG 设置 | 3 | common_tasks §4 | 有设置方法，缺CRS检测 | 加 CRS 检测函数 |
| 7 | 图层顺序控制 | 1 | — | 只提及，无具体操作 | 补充 QgsLayerTree 操作 |
| 8 | 图层样式设置 | 2 | common_tasks §5 | 有分级渲染示例，简单 | 补充分类/单一符号/热力图示例 |
| 9 | QML 样式加载 | 4 | apply_style_qml.py | 完整模板 | — |
| 10 | 矢量裁剪 | 4 | vector_clip_buffer_intersect.py | processing.run | — |
| 11 | 缓冲区 | 4 | vector_clip_buffer_intersect.py | processing.run | — |
| 12 | 相交分析 | 4 | vector_clip_buffer_intersect.py | processing.run | — |
| 13 | 属性筛选 | 1 | — | 未覆盖 | 补充 setSubsetString 示例 |
| 14 | 字段计算 | 0 | — | 未覆盖 | 补充 field calculator 示例 |
| 15 | 栅格裁剪 | 4 | raster_clip_reproject.py | gdal:cliprasterbymasklayer | — |
| 16 | 栅格重投影 | 4 | raster_clip_reproject.py | gdal:warpreproject | — |
| 17 | DEM 坡度 | 4 | raster_clip_reproject.py | native:slope | — |
| 18 | DEM 山影 | 4 | raster_clip_reproject.py | native:hillshade | — |
| 19 | 栅格渲染 | 2 | common_tasks §12 | 只有山影/坡度，缺分级渲染 | 补充单波段伪彩色/多波段渲染 |
| 20 | 标注设置 | 3 | common_tasks §13 | PyQGIS 标注示例 | — |
| 21 | 图例设置 | 3 | create_layout_export_png_pdf.py | QgsLayoutItemLegend | — |
| 22 | 比例尺设置 | 3 | create_layout_export_png_pdf.py | QgsLayoutItemScaleBar | — |
| 23 | 指北针设置 | 1 | — | 未覆盖 | 补充 QgsLayoutItemPicture (north arrow) |
| 24 | 标题和注记 | 3 | create_layout_export_png_pdf.py | QgsLayoutItemLabel | — |
| 25 | Print Layout 自动创建 | 3 | create_layout_export_png_pdf.py | 基础创建 | — |
| 26 | 导出 PNG | 4 | create_layout_export_png_pdf.py | dpi设置+错误处理 | — |
| 27 | 导出 PDF | 4 | create_layout_export_png_pdf.py | 完整导出 | — |
| 28 | 批量导出地图 | 4 | batch_export_maps.py | 按字段分组 | — |
| 29 | 项目保存 | 4 | project_save_and_package.py | 含project info | — |
| 30 | 项目打包 | 4 | project_save_and_package.py | zip archive | — |
| 31 | 错误恢复 | 2 | common_tasks §25 | 只有常见错误表 | 补充逐操作错误处理模板 |
| 32 | 失败后日志记录 | 0 | — | 未覆盖 | 补充 logging 模板 |
| 33 | 输入数据检查 | 2 | 各模板 | 有 check_input() | 统一到工具函数 |
| 34 | 输出成果验收 | 2 | claude_instruction_template.md | 验收清单形式 | 补充自动验收脚本 |
| 35 | 截图/成果图对比 | 3 | computer_use_qgis_steps.md §10 | Codex 截图步骤 | — |

## 综合评分

| 类别 | 平均分 |
|------|:-----:|
| 项目/图层加载 (1-5) | 3.2 |
| CRS/样式 (6-9) | 2.5 |
| 矢量处理 (10-14) | 2.6 |
| 栅格处理 (15-19) | 3.6 |
| 地图元素 (20-24) | 2.6 |
| 布局导出 (25-28) | 3.5 |
| 项目保存 (29-30) | 4.0 |
| 质量保障 (31-35) | 1.8 |
| **总平均** | **2.9 / 5** |
