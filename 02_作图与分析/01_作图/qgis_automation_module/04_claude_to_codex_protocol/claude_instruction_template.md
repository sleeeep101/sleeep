# Claude → Codex 标准指令模板

> Claude 每次发给 Codex 的 QGIS 作图任务，必须遵循此模板

---

## 执行者规则（固化）

- **Claude：** 只负责生成指令，不直接作图。
- **Codex：** 使用 computer use 执行 QGIS 作图（唯一执行者）。
- **用户：** 不承担手动替代执行。
- **Codex 不可用：** 立即暂停作图，只生成待执行任务包。
- **Codex 额度耗尽：** 立即暂停作图。
- **QGIS 不可用：** 暂停 QGIS 作图。

---

## 本地操作依据

Codex 执行时必须参考以下本地文件：
- `qgis_common_tasks.md` — 25项操作手册
- `qgis_vector_workflow.md` — 矢量处理工作流
- `qgis_raster_workflow.md` — 栅格处理工作流
- `qgis_layout_export_manual.md` — 布局与导出
- `qgis_cartography_style_guide.md` — 制图样式指南
- `qgis_error_recovery.md` — 错误恢复
- `03_pyqgis_templates/` — 12个 PyQGIS 模板

---

## 指令格式

```
【任务目标】
(一句话说明要画什么图、做什么分析)

【输入数据】
| 文件路径 | 类型 | 说明 |
|----------|------|------|
| /path/to/data.shp | 矢量 | xxx |
| /path/to/dem.tif | 栅格 | xxx |

【输出要求】
| 输出路径 | 格式 | 说明 |
|----------|------|------|
| /path/to/output.png | PNG (300dpi) | 最终地图 |
| /path/to/project.qgz | QGS | 项目文件 |

【地图元素】
- 标题: xxx
- 图层顺序 (从下到上): xxx
- 配色方案: xxx (如 Blues/Greens/RdYlGn/自定义HEX)
- 样式类型: 单一符号 / 分类 / 渐变 / 热力图
- 图例: 是/否
- 比例尺: 是/否
- 指北针: 是/否
- 标注: 字段名 xxx
- 坐标系: EPSG:xxxx
- 范围: (如需要特定范围)

【Codex 额度状态】
- 正常: 交给 Codex 执行 QGIS 作图
- 已耗尽: 不执行作图，只生成待执行任务包（见 codex_waiting_task_package_template.md）

【额度耗尽时的处理】
- 暂停实际作图
- 不提供用户手动执行步骤
- 不生成 PyQGIS 粘贴执行方案
- 不生成 qgis_process 替代方案
- 保存任务包，等待额度恢复

【操作方式优先级】
1. 使用本地 qgis_automation_module/02_operation_manuals/ 操作手册
2. 使用 03_pyqgis_templates/ 模板
3. 使用 Computer Use 操作 QGIS GUI

【验收标准】
- [ ] 输出文件是否生成
- [ ] 图层是否正确加载
- [ ] CRS 是否正确
- [ ] 图例是否存在
- [ ] 输出图是否可打开
- [ ] 过程是否记录到日志

【完成判定】
必须同时满足：
1. Codex 实际执行（有 computer use 操作过程）
2. 有 Codex 执行日志
3. 有输出文件（PNG/PDF/QGZ）
4. 有截图或导出图
5. 输入→处理→输出关系可追溯
6. 验收标准全部通过
7. 失败不能写成完成

【禁止事项】
- 不删除原始数据
- 不覆盖已有成果
- 不联网下载未知插件
- 不修改系统 QGIS 配置
- 不把失败步骤伪装成成功
- 不提供用户手动执行方案
- Claude 不直接本地作图
- 不用 Python/截图拼接/伪地图替代 Codex 作图
- Codex 不可用时不伪造输出
- 如失败，明确报告失败原因和已尝试的步骤
```

## 示例

```
【任务目标】
基于 DEM 数据生成山影渲染图，叠加河流矢量线

【输入数据】
| <LOCAL_PATH> | 栅格 | 黄土高原 DEM 30m |
| <LOCAL_PATH> | 矢量 | 河流线 |

【输出要求】
| <LOCAL_PATH> | PNG (300dpi) | 山影+河流叠加图 |

【地图元素】
- 标题: 黄土高原地形与河网
- 图例: 是 (河流)
- 比例尺: 是
- 指北针: 是
- 坐标系: EPSG:4326

【Codex 额度状态】正常

【操作方式优先级】
1. 使用 raster_clip_reproject.py 生成山影
2. 使用 create_layout_export_png_pdf.py 创建布局并导出
```
