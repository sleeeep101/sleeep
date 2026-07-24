# Codex Computer Use: QGIS 操作步骤

> Codex 通过 Computer Use 执行 QGIS 操作的标准步骤

## 核心规则

1. **Codex 是唯一实际 QGIS 执行者。** Claude 不直接操作 QGIS。
2. **如果无法使用 computer use，立即停止。** 不要求用户接手。
3. **不把 Claude 生成的静态文件当作真实作图成果。**
4. **每一步必须记录日志。**
5. **每个成果必须有路径。**

---

## 1. 打开 QGIS

1. **检查 QGIS 是否已安装:** 搜索开始菜单 "QGIS" 或检查 `<LOCAL_PATH> Files\QGIS*`
2. **启动:** 双击 QGIS 桌面图标或通过开始菜单启动
3. **等待加载:** QGIS 启动约需 10-30 秒，等待主窗口完全显示
4. **确认版本:** Help → About → 记录版本号 (如 QGIS 3.34.x)

## 2. 确认 QGIS 版本

1. 顶部菜单 Help → About
2. 截图记录版本号
3. 不同版本 Processing 算法名称可能不同

## 3. 打开 Python 控制台

1. 顶部菜单 Plugins → Python Console
2. 或快捷键 Ctrl+Alt+P
3. 确保控制台可见
4. 点击 "Show Editor" 按钮打开脚本编辑器 (可粘贴多行)

## 4. 加载图层

### 方式 A: 拖拽文件到 QGIS 窗口
1. 打开文件资源管理器，定位到数据文件
2. 拖拽 .shp / .tif / .gpkg 文件到 QGIS 地图窗口
3. 检查 Layers 面板是否出现新图层

### 方式 B: 菜单加载
1. Layer → Add Layer → Add Vector Layer (或 Add Raster Layer)
2. 浏览到文件路径 → 点击 Add

### 方式 C: PyQGIS 控制台
1. 打开 Python 控制台
2. 粘贴 `load_vector_layer.py` 或 `load_raster_layer.py` 模板代码
3. 修改文件路径为实际路径
4. 回车执行

## 5. 运行 PyQGIS 脚本

1. 打开 Python 控制台 (Ctrl+Alt+P)
2. 点击 "Show Editor" 按钮
3. 粘贴脚本内容
4. 点击 "Run Script" (绿色三角形) 或 Ctrl+Enter
5. 查看控制台输出确认成功/失败

## 6. 打开 Processing Toolbox

1. 顶部菜单 Processing → Toolbox
2. 或 Ctrl+Alt+T
3. 搜索需要的算法 (如 "clip", "buffer", "hillshade")
4. 双击算法 → 设置参数 → Run

## 7. 创建 Print Layout

1. Project → New Print Layout
2. 输入布局名称
3. 右侧面板: Add Item → Add Map
4. 在画布上拖拽出矩形
5. Add Item → Add Legend
6. Add Item → Add Scale Bar

## 8. 导出地图

1. 在 Print Layout 窗口中: Layout → Export as Image (或 Export as PDF)
2. 选择输出路径
3. 设置分辨率 (通常 300 dpi)
4. 点击 Save

### PyQGIS 导出:
1. 使用 `create_layout_export_png_pdf.py` 模板
2. 修改输出路径

## 9. 保存项目

1. Project → Save (Ctrl+S)
2. 选择 .qgz 格式
3. 或使用 `project_save_and_package.py` 模板

## 10. 截图检查结果

1. 确认地图显示正确
2. 使用截图工具 (Win+Shift+S) 截图
3. 截图保存到输出目录供 Claude 验证

## 11. 把错误信息回传给 Claude

1. 如果 Python 控制台报错，全选→复制错误文本
2. 如果 Processing 失败，复制 Log 标签页内容
3. 粘贴到对话中发给 Claude
4. **不要猜测修复方案，先报告原始错误**

## 12. 在 GUI 卡住时停止操作

1. 如果 QGIS 无响应超过 2 分钟: 打开任务管理器 → 结束 QGIS 进程
2. 如果有未保存工作: 等待更长时间 (最多 5 分钟)
3. 重新启动 QGIS 后先保存当前状态
4. 报告卡住前的最后操作给 Claude

## 13. 避免误删数据

1. **永远不要**在 Processing 中勾选 "Open output file after running algorithm" 的同时覆盖源文件
2. 输出路径始终使用新文件名或新目录
3. 处理前确认输入路径和目标路径不同
4. 不确定时先查看文件内容再操作
