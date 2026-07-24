# QGIS 操作技能卡片

## 操作卡：加载矢量图层
- **触发需求:** 用户提供了 shp/gpkg/geojson 数据
- **输入:** 矢量文件路径
- **输出:** QGIS 图层对象 + 要素计数 + CRS
- **优先模板:** load_vector_layer.py
- **Codex 依据:** computer_use_qgis_steps.md §4
- **验收标准:** layer.isValid()=True;featureCount()>0;crs已识别
- **常见失败:** 文件不存在;编码问题;格式不支持

## 操作卡：加载栅格图层
- **触发需求:** 用户提供了 tif/img 数据
- **输入:** 栅格文件路径
- **输出:** QGIS 栅格图层 + 尺寸 + 波段数 + CRS
- **优先模板:** load_raster_layer.py
- **验收标准:** isValid()=True;width/height>0;crs已识别

## 操作卡：矢量裁剪+缓冲+相交
- **触发需求:** 需要空间分析处理
- **输入:** 源矢量 + 裁剪边界
- **输出:** 处理结果 GeoPackage
- **优先模板:** vector_clip_buffer_intersect.py
- **验收标准:** 输出文件存在;要素数合理

## 操作卡：MCP远程操控（2026-07-21 新增，截图不可靠，仅用于图层操作+PyQGIS执行）
- **触发需求:** 需要 Claude 直接操控 QGIS 加图层/跑代码
- **架构:** MCP Server ←TCP→ QGIS Bridge 插件
- **可靠能力:** ping 连通测试、list_layers 图层查询、add_raster_layer/add_vector_layer、set_canvas_extent 缩放、execute_code 执行任意 PyQGIS
- **不可靠能力:** screenshot 截图（偶发空白，原因：OSM瓦片异步加载未完成即截取，或canvas未渲染）
- **替代方案:** 截图用 QGIS 自带 Project→Export Map to Image；导出用 create_layout_export_png_pdf.py 模板
- **安装:** QGIS → 插件 → 勾选 QGIS MCP Bridge；MCP 配置见 CLAUDE.md
- **验收标准:** ping返回ok；execute_code返回值非None且无error；截图不用此方案

## 操作卡：DEM→山影+坡度
- **触发需求:** 地形分析制图
- **输入:** DEM GeoTIFF
- **输出:** 山影 TIFF + 坡度 TIFF
- **优先模板:** raster_clip_reproject.py
- **验收标准:** 输出文件存在;山影可见;坡度值0-90

## 操作卡：Print Layout 导出
- **触发需求:** 需要输出正式地图
- **输入:** QGIS 项目 + 图层
- **输出:** PNG (300dpi) + PDF
- **优先模板:** create_layout_export_png_pdf.py
- **验收标准:** 输出文件存在可打开;地图元素齐全

## 操作卡：属性筛选+字段计算
- **触发需求:** 按条件筛选 + 计算新字段
- **输入:** 矢量 + 表达式
- **输出:** 筛选结果 GeoPackage
- **优先模板:** attribute_filter_and_field_calc.py
- **验收标准:** 筛选结果正确;新字段值有效

## 操作卡：样式渲染
- **触发需求:** 分类/渐变/单一符号显示
- **输入:** 图层 + 样式参数
- **输出:** 样式化图层
- **优先模板:** apply_style_qml.py (QML) / categorized_graduated_style.py (代码)
- **验收标准:** 图层渲染正确;分类色可区分

## 操作卡：批量导出
- **触发需求:** 按字段分组导出多张地图
- **输入:** 矢量 + 分组字段
- **输出:** 多张 PNG
- **优先模板:** batch_export_maps.py
- **验收标准:** N张PNG存在;命名正确

## 操作卡：指北针+日志
- **触发需求:** 添加指北针 + 记录执行日志
- **输入:** Print Layout + 日志路径
- **输出:** 指北针 + JSON 日志
- **优先模板:** add_north_arrow_and_log.py
- **验收标准:** 指北针可见;日志JSON有效

## 操作卡：项目保存与打包
- **触发需求:** 保存工作成果
- **输入:** QGIS 项目
- **输出:** .qgz + .zip
- **优先模板:** project_save_and_package.py
- **验收标准:** 项目可重新打开;zip包含所有文件
