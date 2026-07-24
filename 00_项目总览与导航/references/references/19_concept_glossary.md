# 19_concept_glossary — 术语/概念库

长期积累 GIS、遥感、统计、ML 等领域的概念解释，避免每次重新查。

每个概念使用固定格式：

```markdown
## 概念：
英文：
所属领域：
一句话解释：
适合初学者的解释：
在 GIS/遥感/空间分析中怎么用：
常见误区：
相关方法：
相关论文：
我当前是否需要掌握：
掌握优先级：
```

---

## GIS/遥感基础

### 数据模型类

| 概念 | 英文 | 一句话 | 优先级 |
|------|------|--------|--------|
| DEM | Digital Elevation Model | 数字高程模型，用栅格每个像元记录地表高程 | 🔴 必须掌握 |
| DSM | Digital Surface Model | 数字表面模型，含建筑物/植被顶部高程 | 🟡 应了解 |
| DTM | Digital Terrain Model | 数字地形模型，裸地表高程 | 🟡 应了解 |
| 栅格 | Raster | 用像元网格表示空间数据 | 🔴 必须掌握 |
| 矢量 | Vector | 用点/线/面几何体表示空间数据 | 🔴 必须掌握 |
| Shapefile | — | ESRI 矢量数据格式（.shp/.shx/.dbf） | 🔴 必须掌握 |
| GeoJSON | — | 基于 JSON 的地理数据交换格式 | 🔴 必须掌握 |
| GeoTIFF | — | 嵌入了地理坐标信息的 TIFF 栅格格式 | 🔴 必须掌握 |

### 坐标与投影类

| 概念 | 英文 | 一句话 | 优先级 |
|------|------|--------|--------|
| 地理坐标系 | Geographic Coordinate System | 用经纬度表示位置（球面坐标） | 🔴 必须掌握 |
| 投影坐标系 | Projected Coordinate System | 把球面展平到平面，用米表示位置 | 🔴 必须掌握 |
| WGS84 | World Geodetic System 1984 | 最常用的地理坐标系，GPS 使用 | 🔴 必须掌握 |
| CGCS2000 | China Geodetic Coordinate System 2000 | 中国大地坐标系 | 🔴 必须掌握 |
| UTM | Universal Transverse Mercator | 通用横轴墨卡托投影，分 60 个带 | 🔴 必须掌握 |
| 空间分辨率 | Spatial Resolution | 一个像元代表的地面大小（如 30m） | 🔴 必须掌握 |

### 空间分析操作类

| 概念 | 英文 | 一句话 | 优先级 |
|------|------|--------|--------|
| 重采样 | Resampling | 改变栅格分辨率（最近邻/双线性/立方卷积） | 🔴 必须掌握 |
| 裁剪 | Clip | 按边界提取数据子集 | 🔴 必须掌握 |
| 叠加分析 | Overlay Analysis | 多个图层叠在一起做空间运算 | 🔴 必须掌握 |
| 缓冲区 | Buffer | 围绕要素生成一定距离的区域 | 🔴 必须掌握 |
| 空间连接 | Spatial Join | 按空间位置关联两个图层的属性 | 🟡 应了解 |
| 拓扑检查 | Topology Check | 检查空间数据是否闭合、重叠、有悬挂线等 | 🟡 应了解 |

---

## 地形/水文/土壤侵蚀

| 概念 | 英文 | 一句话 | 优先级 |
|------|------|--------|--------|
| 坡度 | Slope | 地表倾斜程度（度或百分比） | 🔴 必须掌握 |
| 坡向 | Aspect | 坡面朝向（0-360°，北为 0/360） | 🔴 必须掌握 |
| 曲率 | Curvature | 地表弯曲程度（剖面曲率/平面曲率） | 🟡 应了解 |
| 汇流累积 | Flow Accumulation | 有多少上游像元的水流向这里 | 🔴 必须掌握 |
| 流向 | Flow Direction | 水往哪个方向流（D8 算法等） | 🔴 必须掌握 |
| 流域 | Watershed / Basin | 由分水岭围成的集水区域 | 🔴 必须掌握 |
| 沟谷 | Gully | 由集中水流侵蚀形成的线状地貌 | 🔴 必须掌握 |
| 地形湿度指数 | TWI (Topographic Wetness Index) | 反映地形对土壤水分空间分布的控制 | 🟡 应了解 |
| LS 因子 | LS Factor | RUSLE 中的坡长坡度因子 | 🔴 必须掌握 |
| RUSLE | Revised Universal Soil Loss Equation | 修正通用土壤流失方程 | 🔴 必须掌握 |
| USLE | Universal Soil Loss Equation | 通用土壤流失方程（RUSLE 前身） | 🟡 应了解 |
| 土壤可蚀性 | Soil Erodibility (K Factor) | 土壤抵抗侵蚀的能力 | 🟡 应了解 |
| 降雨侵蚀力 | Rainfall Erosivity (R Factor) | 降雨引起土壤侵蚀的潜在能力 | 🟡 应了解 |

---

## 遥感指数与分类

| 概念 | 英文 | 一句话 | 优先级 |
|------|------|--------|--------|
| NDVI | Normalized Difference Vegetation Index | 归一化植被指数，(NIR-R)/(NIR+R) | 🔴 必须掌握 |
| EVI | Enhanced Vegetation Index | 增强植被指数，减土壤/大气影响 | 🟡 应了解 |
| NDBI | Normalized Difference Built-up Index | 归一化建筑指数 | 🟢 知道就行 |
| NDWI | Normalized Difference Water Index | 归一化水体指数 | 🟢 知道就行 |
| 土地利用/土地覆盖 | LULC (Land Use/Land Cover) | 地表覆盖类型分类 | 🔴 必须掌握 |
| 监督分类 | Supervised Classification | 有训练样本的分类 | 🔴 必须掌握 |
| 非监督分类 | Unsupervised Classification | 无训练样本的聚类分类 | 🟡 应了解 |
| 变化检测 | Change Detection | 多时相影像对比分析地表变化 | 🟡 应了解 |
| 混淆矩阵 | Confusion Matrix | 分类结果 vs 真实类别的交叉表 | 🔴 必须掌握 |
| Kappa 系数 | Kappa Coefficient | 分类一致性指标（去除随机一致） | 🔴 必须掌握 |
| 总体精度 | Overall Accuracy (OA) | 分类正确的像元占比 | 🔴 必须掌握 |
| F1 | F1 Score | 精确率和召回率的调和平均 | 🟡 应了解 |

---

## 空间统计与建模

| 概念 | 英文 | 一句话 | 优先级 |
|------|------|--------|--------|
| 空间自相关 | Spatial Autocorrelation | 邻近位置的值是否相似 | 🟡 应了解 |
| Moran's I | — | 度量全局空间自相关的指标（-1~1） | 🟡 应了解 |
| LISA | Local Indicators of Spatial Association | 局部空间自相关（局部 Moran's I） | 🟡 应了解 |
| 热点分析 | Hot Spot Analysis (Getis-Ord Gi*) | 识别高值/低值聚集区 | 🟡 应了解 |
| GWR | Geographically Weighted Regression | 地理加权回归——系数随位置变化 | 🟡 应了解 |
| MGWR | Multiscale GWR | 多尺度地理加权回归 | 🟢 知道就行 |
| 地理探测器 | Geodetector | 探测空间分异性及其驱动力 | 🟡 应了解 |
| 空间滞后模型 | Spatial Lag Model (SLM) | 因变量受邻近区域因变量影响 | 🟢 知道就行 |
| 空间误差模型 | Spatial Error Model (SEM) | 误差项存在空间自相关 | 🟢 知道就行 |
| MAUP | Modifiable Areal Unit Problem | 可塑面积单元问题——结果随分区方式而变 | 🟡 应了解 |

---

## 机器学习与实验设计

| 概念 | 英文 | 一句话 | 优先级 |
|------|------|--------|--------|
| Baseline | — | 作为比较基准的简单方法/模型 | 🔴 必须掌握 |
| 训练集/验证集/测试集 | Train/Val/Test Split | 数据划分：训练模型/调参/最终评估 | 🔴 必须掌握 |
| 交叉验证 | Cross-Validation | 多次划分训练/验证以减少偶然性 | 🟡 应了解 |
| 空间交叉验证 | Spatial CV | 按空间块划分防止空间自相关泄露 | 🟡 应了解 |
| 过拟合 | Overfitting | 模型记住了训练数据的噪声而非规律 | 🔴 必须掌握 |
| 欠拟合 | Underfitting | 模型太简单没学到足够规律 | 🟡 应了解 |
| 特征工程 | Feature Engineering | 从原始数据构造有用特征 | 🟡 应了解 |
| 消融实验 | Ablation Study | 逐个去掉组件证明每个都有用 | 🟡 应了解 |
| SHAP | SHapley Additive exPlanations | 解释每个特征对预测的贡献 | 🟢 知道就行 |
| AUC | Area Under ROC Curve | 分类器整体区分能力的指标 | 🟡 应了解 |
| RMSE | Root Mean Square Error | 均方根误差（回归评估指标） | 🔴 必须掌握 |
| MAE | Mean Absolute Error | 平均绝对误差（回归评估指标） | 🟡 应了解 |

---

## 使用规则

1. **每次遇到新概念** → 判断是否该加入概念库
2. **入概念库的门槛**：GIS/遥感/统计/ML 领域核心概念；或论文中反复出现但我还不熟悉的概念
3. **初学版解释** 必须用非学术语言，假设读者只有高中基础
4. **定期回顾**：每周复盘时快速浏览本库新增条目
5. **标注优先级**：🔴 必须掌握 > 🟡 应了解 > 🟢 知道就行
