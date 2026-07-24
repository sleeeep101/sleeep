# 作图与分析

> QGIS自动化制图 / Origin科学绑图 / 数据可视化 | 最后更新: 2026-07-24

## 目录结构

```
02_作图与分析/
├── 00_core_scripts/        # Origin绑图提示词 + QGIS自动化核心
├── 01_作图/                # QGIS自动化模块 + Origin绑图
│   ├── origin_auto_plot/   # Origin自动绑图
│   └── qgis_automation_module/  # QGIS自动化
└── README.md              # 本文件
```

## 输出规范

### 图片分级

| 级别 | 用途 | 分辨率 | 格式 | 示例 |
|------|------|--------|------|------|
| **T1 发表级** | 期刊投稿 | ≥300 DPI | TIFF/EPS | 论文主图 |
| **T2 汇报级** | 组会PPT/开题 | 150-200 DPI | PNG | PPT配图 |
| **T3 草稿级** | 内部讨论 | 72 DPI | PNG/JPG | 快速验证 |

### 命名规范

```
{项目简称}_{内容}_{日期}_{版本}.{格式}
例: rusle_坡度因子图_20260724_v1.png
```

### 配色规范

- 学术论文：灰度优先（Color Universal Design），确保黑白打印可读
- 组会PPT：品牌色+对比色
- 所有图必须包含：标题、坐标轴标签(含单位)、图例、比例尺(地图)、指北针(地图)

### 发布前的可复现性与隐私检查（2026-07-24，参考 SciencePlots 实践）

- 每张拟提交或共享的图都应有同名 `figure_manifest.json`：记录相对路径的数据来源、可公开校验值、数据访问级别（`public`/`restricted`/`synthetic`）、渲染脚本、软件版本、输出格式和分辨率。受限数据必须说明不含敏感位置、主体或原始记录的公开说明。
- 禁止在清单中写入 `<LOCAL_PATH>`、用户名目录、网盘绝对路径、联系人或受限数据位置；受限数据只记录授权状态和可公开替代说明。
- 期刊主图至少 300 DPI；输出文件扩展名必须与清单格式一致；地图清单应记录 CRS。色标、单位、分级方法和缺失值样式须在同一稿件内固定。
- 提交前运行 `python 01_作图/figure_release_gate.py --manifest figure_manifest.json --figure-dir .`，再运行既有跨图颜色审计。检查通过仅说明元数据完整，不代表统计或因果结论成立。

## GIS制图规则

- **坐标系必须统一**：所有图层使用相同CRS，投影坐标系用于面积/距离计算
- **空间索引**：大型矢量数据（>1000要素）创建空间索引
- **输出检查**：运行 `python 01_读_论文阅读与复盘/00_core_scripts/check_gis_data.py --code script.py`
- **数据源标注**：底图数据注明来源（Natural Earth / OSM / 自采）

## QGIS自动化

`qgis_automation_module/` 批量制图脚本。输出 → `task_results/` 目录。

## Origin绑图

`origin_auto_plot/` 模板 + `00_core_scripts/origin_auto_plot_prompt.md` 提示词。

## 当前策略

基于 QGIS Python API 的全自动制图管线。每次制图任务应有明确的需求描述（输出格式、分辨率、配色、标注要求）。

*最后更新: 2026-07-24*
