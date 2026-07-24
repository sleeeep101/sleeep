# Claude → Codex 作图指令

> 基于模板: `claude_instruction_template.md`

---

【任务目标】
使用 Natural Earth 公开数据制作"中国及周边主要城市专题图"，生成操作前/后对比图。

【输入数据】
| 文件路径 | 类型 | 说明 |
|---------|------|------|
| input_raw/ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp | 矢量面 | 世界国家边界 |
| input_raw/ne_110m_populated_places_simple/ne_110m_populated_places_simple.shp | 矢量点 | 主要城市 |

【输出要求】
| 输出路径 | 格式 | 说明 |
|---------|------|------|
| before_preview/before_preview.png | PNG (150dpi) | 原始数据默认样式全球预览 |
| after_outputs/after_map.png | PNG (300dpi) | 中国及周边专题图 |
| after_outputs/after_map.pdf | PDF | 同上 |
| after_outputs/after_project.qgz | QGS | 项目文件 |
| after_outputs/before_after_comparison.png | PNG | 左侧before右侧after对比图 |

【地图元素】
- 标题: 中国及周边主要城市专题图
- 图层顺序 (从下到上): 国家面 → 河流(可选) → 城市点
- 配色方案: 中国边界红色加粗; 其他国家浅灰参考; 城市按 scalerank 分类
- 样式类型: 分类 (国家边界: 中国 vs 其他; 城市: 按 scalerank 大小和颜色)
- 图例: 是
- 比例尺: 是
- 指北针: 是
- 标注: 首都/主要城市名称 (NAME 字段)
- 坐标系: EPSG:4326
- 范围: 中国及周边 (lon: 70-140, lat: 15-55)

【Codex 额度状态】
等待 Codex + QGIS 环境就绪

【操作方式优先级】
1. 使用本地 qgis_automation_module/02_operation_manuals/ 操作手册
2. 使用 03_pyqgis_templates/ 模板 (优先 create_layout_export_png_pdf.py + categorized_graduated_style.py + attribute_filter_and_field_calc.py)
3. 使用 Computer Use 操作 QGIS GUI

【验收标准】
- [ ] before_preview.png 存在 — 全球默认样式
- [ ] after_map.png 存在 — 中国及周边专题图
- [ ] after_map.pdf 存在
- [ ] after_project.qgz 存在
- [ ] before_after_comparison.png 存在
- [ ] 前后图同源 (同一批 Natural Earth 数据)
- [ ] 原始文件 SHA256 未变化
- [ ] 操作后图包含标题/图例/比例尺/指北针
- [ ] 中国边界明显区分于其他国家

【禁止事项】
- 不删除原始数据
- 不覆盖原始下载文件
- 不使用无关图片作为对比
- 不伪造成果
- Codex 额度耗尽时暂停，不提供手动替代
