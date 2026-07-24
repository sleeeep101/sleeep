"""
知识图谱全局配置
===============
所有路径、正则 pattern、实体/关系类型常量。
"""

import os

# ── 根路径 ─────────────────────────────────────────────
ACADEMIC_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # academic-workflow/
KG_ROOT = os.path.dirname(os.path.abspath(__file__))  # knowledge_graph/
PROJECT_ROOT = os.path.dirname(ACADEMIC_ROOT)  # <LOCAL_PATH>

# ── 数据源路径 ─────────────────────────────────────────
LONG_TERM_KB = os.path.join(ACADEMIC_ROOT, "01_读_论文阅读与复盘", "04_长期知识库", "长期知识库.md")
TERMINOLOGY_DB = os.path.join(ACADEMIC_ROOT, "01_读_论文阅读与复盘", "04_长期知识库", "专业术语库.md")
TECHNIQUE_DB = os.path.join(ACADEMIC_ROOT, "01_读_论文阅读与复盘", "04_长期知识库", "学术写作技法库.md")
INNOVATION_DB = os.path.join(ACADEMIC_ROOT, "01_读_论文阅读与复盘", "04_长期知识库", "可能的创新点.md")
DAILY_REPORTS_DIR = os.path.join(ACADEMIC_ROOT, "01_读_论文阅读与复盘", "01_每日论文")
REASONING_LENS = os.path.join(ACADEMIC_ROOT, "references", "universaldistill", "reasoning-lens.md")
SPATIAL_GUARDRAILS = os.path.join(ACADEMIC_ROOT, "references", "gis", "spatial-analysis-guardrails.md")
GRADING_CONFIG = os.path.join(ACADEMIC_ROOT, "config", "paper_grading_config.json")
PATHS_CONFIG = os.path.join(ACADEMIC_ROOT, "config", "paths.json")
PERSONAL_BRAIN_DAILY = os.path.join(PROJECT_ROOT, "Personal-Brain", "reports", "daily")

# ── 图谱存储 ───────────────────────────────────────────
KG_DATA_FILE = os.path.join(KG_ROOT, "kg_data.json")
KG_HASH_CACHE = os.path.join(KG_ROOT, ".kg_hash_cache.json")

# ── 实体类型 ───────────────────────────────────────────
ENTITY_TYPES = [
    "Paper",
    "Term",
    "Technique",
    "Innovation",
    "DailyReport",
    "Method",
    "Concept",
    "Guardrail",
    "Script",
    "ResearchDirection",
]

# ── 关系类型 ───────────────────────────────────────────
RELATION_TYPES = {
    "INTRODUCES": ("Paper", "Term"),
    "USES_METHOD": ("Paper", "Method"),
    "EXEMPLIFIES": ("Paper", "Technique"),
    "BELONGS_TO": ("Paper", "ResearchDirection"),
    "RELATED_TO": ("Term", "Term"),
    "USED_IN": ("Term", "Method"),
    "CATEGORIZED_AS": ("Term", "Category"),
    "DERIVED_FROM": ("Technique", "Paper"),
    "USES_TERM": ("Technique", "Term"),
    "COMPLEMENTS": ("Technique", "Technique"),
    "SOURCED_FROM": ("Innovation", "Paper"),
    "REPORTED_IN": ("Innovation", "DailyReport"),
    "SUITABLE_FOR": ("Innovation", "ResearchDirection"),
    "GENERATED": ("DailyReport", "Paper"),
    "COVERS": ("DailyReport", "ResearchDirection"),
    "APPLIES_TO": ("Concept", "Paper"),
    "FRAMES": ("Concept", "Term"),
    "APPLIES_TO_METHOD": ("Guardrail", "Method"),
    "CITES": ("Guardrail", "Term"),
    "PRODUCES": ("Script", "DailyReport"),
    "READS": ("Script", "ResearchDirection"),
}

# ── 知识库 Markdown 解析 Pattern ─────────────────────
# KB 条目 header: ### KB-2026-07-21-01 | 论文标题
KB_HEADER_PATTERN = r"^###\s+(KB-\d{4}-\d{2}-\d{2}-\d{2,3})\s*[|｜]\s*(.+)"
# Paper_ID 格式（旧格式）: ### Paper_ID: 2026-06-07_F01
PAPER_ID_HEADER_PATTERN = r"^###\s+Paper_ID:\s*(\d{4}-\d{2}-\d{2}_F\d{2,3})"

# 术语 header: ### A-001｜面积高程积分（Hypsometric Integral, HI）
TERM_HEADER_PATTERN = r"^###\s+([A-Z])-(\d{3})\s*[｜|]\s*(.+)$"

# 技法 header: ### 技法-Method-001｜模型选择的三段式论证
TECHNIQUE_HEADER_PATTERN = r"^###\s+技法-([A-Za-z]+)-(\d{3})\s*[｜|]\s*(.+)"

# 创新点 header: ### INNO-2026-06-22-01
INNOVATION_HEADER_PATTERN = r"^###\s+(INNO-\d{4}-\d{2}-\d{2}-\d{2,3})\s*$"

# 日报文件名: YYYY-MM-DD_论文阅读日报.md
DAILY_REPORT_FILENAME_PATTERN = r"^(\d{4}-\d{2}-\d{2})_论文阅读日报\.md$"

# 项目监管日报: YYYY-MM-DD_每日项目监管报告.md
SUPERVISION_REPORT_FILENAME_PATTERN = r"^(\d{4}-\d{2}-\d{2})_每日项目监管报告\.md$"

# 字段提取: - **字段名:** 值
FIELD_PATTERN = r"^-\s+\*\*(.+?)\*\*\s*(.*)$"

# Wiki-link: [[长期知识库#KB-xxx]] 或 [[2026-06-22_论文阅读日报]]
WIKI_LINK_PATTERN = r"\[\[([^\]]+)\]\]"

# ── 术语分类映射 ───────────────────────────────────────
TERM_CATEGORY_MAP = {
    "A": "DEM与数字地形分析",
    "B": "GIS与空间分析",
    "C": "遥感与InSAR",
    "D": "土壤侵蚀与水土保持",
    "E": "地貌与地质分析",
    "F": "生态与生物地球化学",
    "G": "统计与方法论",
    "H": "水文与水资源",
    "I": "气候与气象",
    "J": "土壤科学",
    "K": "测绘与测量",
    "L": "地质与年代学",
    "M": "AI与深度学习",
    "Z": "交叉/其他",
}

# ── 技法分类映射 ───────────────────────────────────────
TECHNIQUE_CATEGORY_MAP = {
    "Abstract": "摘要与引言",
    "Intro": "摘要与引言",
    "Method": "方法与数据描述",
    "Result": "结果呈现",
    "Discuss": "讨论与论证",
    "Figure": "图表描述",
    "Cite": "引用整合",
    "Trans": "过渡与衔接",
    "GIS": "GIS/遥感/DEM特有技法",
}

# ── IMRaD 分类 ─────────────────────────────────────────
IMRAD_SECTIONS = [
    "标题", "引言", "方法", "结果", "讨论", "图表", "引用", "过渡", "GIS特有"
]

# ── 可视化颜色映射 ─────────────────────────────────────
ENTITY_COLORS = {
    "Paper": "#4A90D9",           # 蓝
    "Term": "#5CB85C",            # 绿
    "Technique": "#F0AD4E",       # 橙
    "Innovation": "#D9534F",      # 红
    "DailyReport": "#9B9B9B",     # 灰
    "Method": "#7B68EE",          # 紫
    "Concept": "#2F4F4F",         # 深灰绿
    "Guardrail": "#C0392B",       # 深红
    "Script": "#3498DB",          # 浅蓝
    "ResearchDirection": "#1ABC9C", # 青
}

# ── 方法关键词 → 标准名映射（从 _shared_constants.py 同步）──
METHOD_KEYWORDS = {
    "random forest": "Random Forest",
    "rf": "Random Forest",
    "xgboost": "XGBoost",
    "xg boost": "XGBoost",
    "support vector machine": "SVM",
    "svm": "SVM",
    "support vector regression": "SVR",
    "svr": "SVR",
    "convolutional neural network": "CNN",
    "cnn": "CNN",
    "deep learning": "Deep Learning",
    "dl": "Deep Learning",
    "artificial neural network": "ANN",
    "ann": "ANN",
    "k-nearest neighbor": "KNN",
    "knn": "KNN",
    "logistic regression": "Logistic Regression",
    "ridge regression": "Ridge Regression",
    "lasso": "LASSO",
    "gradient boosting": "Gradient Boosting",
    "gbm": "Gradient Boosting",
    "principal component analysis": "PCA",
    "pca": "PCA",
    "k-means": "K-Means",
    "dbscan": "DBSCAN",
    "maxent": "MaxEnt",
    "geographically weighted regression": "GWR",
    "gwr": "GWR",
    "moran's i": "Moran's I",
    "inverse distance weighting": "IDW",
    "idw": "IDW",
    "kriging": "Kriging",
    "ordinary kriging": "Ordinary Kriging",
    "universal kriging": "Universal Kriging",
    "rusle": "RUSLE",
    "usle": "USLE",
    "invest": "InVEST",
    "invest sdr": "InVEST SDR",
    "swat": "SWAT",
    "sentinel-2": "Sentinel-2",
    "sentinel-1": "Sentinel-1",
    "landsat": "Landsat",
    "uav": "UAV",
    "sfm": "SfM",
    "structure from motion": "SfM",
    "lidar": "LiDAR",
    "terrestrial laser scanning": "TLS",
    "tls": "TLS",
    "point cloud": "Point Cloud",
    "object-based image analysis": "OBIA",
    "obia": "OBIA",
    "change detection": "Change Detection",
    "time series analysis": "Time Series Analysis",
    "markov chain": "Markov Chain",
    "cellular automata": "Cellular Automata",
    "analytic hierarchy process": "AHP",
    "ahp": "AHP",
    "frequency ratio": "Frequency Ratio",
    "fr": "Frequency Ratio",
    "information value": "Information Value",
    "iv": "Information Value",
    "weight of evidence": "Weight of Evidence",
    "woe": "Weight of Evidence",
    "certainty factor": "Certainty Factor",
    "cf": "Certainty Factor",
    "boosted regression tree": "Boosted Regression Tree",
    "brt": "Boosted Regression Tree",
    "bart": "Bayesian Additive Regression Tree",
    "multivariate adaptive regression splines": "MARS",
    "mars": "MARS",
    "copras": "COPRAS",
    "swara": "SWARA",
    "adaboost": "AdaBoost",
    "kernel logistic regression": "KLR",
    "klr": "KLR",
    "credal decision tree": "CDTree",
    "cdtree": "CDTree",
    "best-first decision tree": "BFTree",
    "bftree": "BFTree",
    "generalized linear model": "GLM",
    "glm": "GLM",
    "generalized additive model": "GAM",
    "gam": "GAM",
}
