# 12_gis_remote_sensing_workflow — GIS/遥感专属流程

## GIS 操作完成标准

参照 `references/16_done_definition.md` 环节 3（ArcGIS/QGIS/GEE 学习完成标准）：

每次 GIS 操作必须满足 6 条才叫完成：
1. 用样例数据完成一次完整操作
2. 导出结果图或截图
3. 记录操作步骤（每一步的菜单/工具/参数）
4. 记录遇到的问题和解决方法
5. 形成一条 GIS 操作卡片
6. 判断该操作以后能否用于导师项目或论文

**操作卡片模板**：
```markdown
### {操作名}
- **软件/工具**: ArcGIS Pro / QGIS / GEE / GDAL / ArcPy
- **输入数据**: {类型、格式、要求}
- **操作步骤**: 1. 2. 3.
- **关键参数**: {参数名=值，原因}
- **输出结果**: {文件类型、内容}
- **遇到的问题**: 1. 2.
- **知识点**: {这次学到的核心概念}
- **可复用于**: {导师项目 / 论文 / 就业}
- **截图**: {路径}
```

**存放到**: `gis_operation_notes/YYYY-MM-DD_操作名_操作记录_v1.md`

## GIS 任务分类与 Codex 拆解指南

遇到 GIS/遥感任务时，Claude 判断任务类型 → 生成规范 → Codex 执行。

### 1. DEM 分析流程

**典型任务**：坡度/坡向/曲率/地形湿度指数/沟谷提取/流域分析
**工具**：ArcPy / QGIS Processing / GDAL / WhiteboxTools / Python
**规范**：
1. 记录 DEM 数据来源、分辨率、坐标系
2. 检查并统一投影（UTM/CGCS2000 视区域而定）
3. 填洼（Fill Sinks）
4. 计算流向 → 汇流累积
5. 目标分析
6. 输出带坐标系信息的 GeoTIFF
**Codex 任务**：给定 DEM 路径和参数，生成分析脚本 + 输出验证

### 2. 遥感分类流程

**典型任务**：土地利用分类/变化检测/植被提取/水体提取
**工具**：GEE / Python(sklearn/pytorch) / ArcGIS / ENVI
**规范**：
1. 记录影像来源、时间、波段、分辨率
2. 预处理：大气校正/几何校正/云掩膜
3. 样本采集与标注
4. 特征提取
5. 模型训练→验证→测试
6. 精度评价（混淆矩阵+Kappa+F1+OA）
7. 输出分类图 + 面积统计
**重要**：训练/测试区域必须空间独立

### 3. 空间数据处理

**典型任务**：投影转换/裁剪/重采样/栅格计算/矢栅转换
**规范**：
1. 输入数据坐标系检查
2. 统一投影（一般用研究区中心经线的 UTM 或 CGCS2000）
3. 统一分辨率
4. 批处理记录脚本

### 4. 坐标系/投影检查清单

```
- [ ] 坐标系: WGS84 / CGCS2000 / 地方坐标系?
- [ ] 投影: UTM 几度带? / Albers / Lambert?
- [ ] 单位: 度(十进制) / 米?
- [ ] 输入和输出坐标系是否一致?
- [ ] 如果是栅格计算，是否已统一投影和分辨率?
```

### 5. 数据来源记录规范

```markdown
## 数据来源
| 数据 | 来源 | 下载链接/方式 | 时间 | 空间范围 | 分辨率 | 坐标系 | 许可证 |
|------|------|-------------|------|---------|--------|--------|--------|
| DEM | NASA SRTM | https://... | 2000 | 全球 | 30m | WGS84 | 开放 |
| Landsat 8 | USGS EarthExplorer | https://... | 2020-2023 | 研究区 | 30m | UTM 50N | 开放 |
```

### 6. 地图输出规范

- 必须有：比例尺、指北针、图例、坐标系标注
- 推荐配色：ColorBrewer 或 cmocean（适合色盲友好）
- 分级设色：Jenks Natural Breaks 或 Quantile
- 分辨率：论文用≥300 DPI
- 文字标注：清晰可读，不用花哨字体

### 7. GIS 任务 → Codex 任务拆解

Claude 输出此模板给 Codex：

```markdown
## GIS 任务：{任务名}
- 输入数据：{路径/来源}
- 目标输出：{文件类型/格式}
- 工具：ArcPy / GDAL / GEE / QGIS
- 坐标系：{目标投影}
- 处理步骤：1. 2. 3.
- 验证方式：{如何检查输出正确}
- 注意事项：{易错点}
```

### 8. GIS 任务分解模式（来源：LLM-Find + AutonomousGIS）

**自然语言 → GIS 操作的标准 7 步分解**：

| 步骤 | 动作 | 示例 |
|------|------|------|
| 1. 任务命名 | 给任务一个明确的名字 | "下载重庆市 30m DEM 数据" |
| 2. 任务拆解 | NL → 结构化 GIS 步骤 | 地名→边界框→选择数据源→构造API→下载→保存GeoTIFF |
| 3. 数据概览 | 检查 CRS/几何类型/范围 | WGS84 经纬度→UTM 投影 |
| 4. 工具选择 | 匹配 QGIS/ArcPy/GDAL 工具 | OpenTopography API / SRTM |
| 5. 处理工作流 | 生成有向图 | Nominatim→OSMnx→OpenTopography→GDAL |
| 6. 代码生成 | LLM 生成 Python 代码 | `download_data()` 函数 |
| 7. 代码调试 | 最多 5 轮 auto-debug | 错误回溯→修复→重跑 |

### 9. 数据源手册模式（来源：LLM-Find）

每个 GIS 数据源维护一个标准化手册，Agent 自动发现和调用：

```toml
# {数据源名}.toml
data_source_name = "OpenTopography"
brief_description = "全球 DEM 数据（SRTM/COP/NASADEM），分辨率 15m-1000m"

[handbook]
api_endpoint = "https://portal.opentopography.org/API/globaldem"
supported_dem_types = ["SRTMGL3", "SRTMGL1", "AW3D30", "NASADEM", "COP30"]
requires_api_key = true
coordinate_system = "WGS84"
output_format = "GeoTIFF"
code_example = '''
import requests
url = f"https://portal.opentopography.org/API/globaldem?demtype={demtype}&south={s}&north={n}&west={w}&east={e}&outputFormat=GTiff&API_Key={key}"
'''
```

**现有可用数据源**（来自 AutonomousGIS）：OpenStreetMap、US Census、COVID-NYT、OpenWeather、ESRI World Imagery、OpenTopography、USGS Earthquake。**国内可用替代**：地理空间数据云、资源环境数据云平台。

### 10. GIS Agent 模型选择策略（来源：AutonomousGIS）

| 调用类型 | 模型要求 | 示例 |
|---------|---------|------|
| 高推理调用 | 强模型（GPT-5/Claude Opus 级别） | 任务拆解、代码生成、调试 |
| 快速调用 | 轻模型（GPT-4o/Haiku 级别） | 工具选择、数据概览、工作流图 |

当前 academic-workflow 中 Claude 做高推理，Codex 做快速代码生成，已对齐此模式。
