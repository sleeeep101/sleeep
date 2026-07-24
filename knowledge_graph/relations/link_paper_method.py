"""
论文 ↔ 方法 关系提取
===================
从论文的 topics/methods 字段匹配方法实体，建立 Paper -[USES_METHOD]-> Method。
"""

import re
from typing import List, Dict, Optional

from ..kg_config import METHOD_KEYWORDS
from ..kg_schema import Method, Paper, Relation


class PaperMethodLinker:
    """论文-方法关系发现"""

    def __init__(self):
        self.method_map = METHOD_KEYWORDS
        self._canonical_cache: Dict[str, str] = {}

    def extract_methods_from_papers(self, papers: List[Paper]) -> List[Method]:
        """从论文中提取所有出现的标准方法"""
        seen_canonical = set()
        methods = []

        for paper in papers:
            # 从 topic 和 methods 字段提取
            search_text = " ".join(paper.topics + paper.methods + [paper.summary])
            found = self._find_method_names(search_text)

            for canonical_name in found:
                if canonical_name not in seen_canonical:
                    seen_canonical.add(canonical_name)
                    methods.append(Method(
                        id=f"method_{canonical_name.lower().replace(' ', '_').replace('-', '_')}",
                        canonical_name=canonical_name,
                        aliases=[],
                        category=self._classify_method(canonical_name),
                    ))

        return methods

    def build_relations(self, papers: List[Paper], methods: List[Method]) -> List[Relation]:
        """建立 Paper → Method 关系"""
        relations = []
        method_index = {m.canonical_name: m for m in methods}

        for paper in papers:
            search_text = " ".join(paper.topics + paper.methods + [paper.summary])
            found = self._find_method_names(search_text)

            for canonical_name in found:
                if canonical_name in method_index:
                    relations.append(Relation(
                        source_id=paper.id,
                        target_id=method_index[canonical_name].id,
                        relation_type="USES_METHOD",
                        confidence=0.85,
                        source_file="link_paper_method",
                        metadata={"method_name": canonical_name},
                    ))

        return relations

    def _find_method_names(self, text: str) -> List[str]:
        """在文本中找所有标准方法名"""
        text_lower = text.lower()
        found = set()

        for keyword, canonical in self.method_map.items():
            if len(keyword) >= 3 and keyword in text_lower:
                found.add(canonical)

        return list(found)

    def _classify_method(self, method_name: str) -> str:
        """分类方法"""
        ml_keywords = ["NN", "CNN", "Deep Learning", "Random Forest", "XGBoost",
                       "SVM", "SVR", "KNN", "Gradient Boosting", "ANN",
                       "Logistic Regression", "Ridge", "LASSO", "PCA",
                       "K-Means", "DBSCAN", "MaxEnt", "AdaBoost", "MARS",
                       "GLM", "GAM", "BRT", "BART", "CDTree", "BFTree", "KLR"]
        gis_keywords = ["GWR", "Moran's I", "IDW", "Kriging", "OBIA"]
        rs_keywords = ["Sentinel", "Landsat", "UAV", "LiDAR", "SfM", "Point Cloud",
                       "Change Detection", "TLS"]
        geo_keywords = ["RUSLE", "USLE", "InVEST", "SWAT", "AHP", "Frequency Ratio",
                        "Information Value", "Weight of Evidence", "Certainty Factor",
                        "COPRAS", "SWARA", "Markov Chain", "Cellular Automata"]

        mn = method_name
        if any(k in mn for k in ml_keywords):
            return "ML"
        if any(k in mn for k in gis_keywords):
            return "GIS"
        if any(k in mn for k in rs_keywords):
            return "RemoteSensing"
        if any(k in mn for k in geo_keywords):
            return "Geomorphology"
        return "Statistics"
