"""
零依赖语义相似度关系发现
=======================
用纯 Python TF-IDF + 余弦相似度连接孤立体到最近邻实体。
不需要任何模型下载，不需要 GPU，不需要 jieba。
"""

import re
import math
from collections import defaultdict, Counter
from typing import List, Dict, Tuple


class SemanticLinker:
    """零依赖语义连接器"""

    def __init__(self, entities: Dict[str, Dict]):
        self.entities = entities
        self._build_index()

    def _build_index(self):
        """构建可搜索的目标实体索引"""
        self.targets: Dict[str, str] = {}  # id → searchable text
        self.target_type: Dict[str, str] = {}  # id → entity_type

        for eid, attrs in self.entities.items():
            etype = attrs.get("entity_type", "")
            if etype in ("Paper", "Term", "ResearchDirection", "Technique", "Guardrail", "Innovation"):
                text = self._make_searchable(attrs)
                if len(text) > 15:
                    self.targets[eid] = text
                    self.target_type[eid] = etype

    def _make_searchable(self, attrs: Dict) -> str:
        """将实体属性拼接为可搜索文本"""
        parts = []
        for key in ("title", "name", "label", "rule", "condition",
                     "summary", "english", "chinese", "explanation",
                     "description", "canonical_name", "domain",
                     "template", "usage"):
            val = attrs.get(key, "")
            if isinstance(val, str) and len(val) > 1:
                # 去掉前导冒号和空白
                cleaned = val.lstrip(":： \t\n")
                if len(cleaned) > 1:
                    parts.append(cleaned)
            elif isinstance(val, list):
                cleaned_list = [str(x).lstrip(":： \t\n") for x in val[:10]
                                if len(str(x).lstrip(":： \t\n")) > 1]
                parts.append(" ".join(cleaned_list))
        return " ".join(parts)

    def extract_all(self) -> List:
        """为每个孤立体找到最近的连接"""
        from ..kg_schema import Relation
        relations = []

        # 0. 同域 Guardrail 互连 + 同源 ResearchDirection 互连
        relations.extend(self._link_same_domain())
        relations.extend(self._link_same_source())

        # 0.5 桌面笔记关键词桥接
        relations.extend(self._link_desktop_by_keywords())

        # 找孤立体
        orphans = []
        for eid, attrs in self.entities.items():
            etype = attrs.get("entity_type", "")
            if etype in ("Guardrail", "Technique", "DailyReport"):
                text = self._make_searchable(attrs)
                if len(text) > 10:  # 放宽：10字符即可
                    orphans.append((eid, etype, text))

        if not orphans:
            return relations

        # 构建 TF-IDF 词汇表
        all_docs = [text for _, _, text in orphans] + list(self.targets.values())
        idf = self._compute_idf(all_docs)

        # 为每个目标文档构建 TF-IDF 向量
        target_vectors = {}
        for tid, ttext in self.targets.items():
            target_vectors[tid] = self._tfidf_vector(ttext, idf)

        # 为每个孤立体找最佳匹配
        for oid, otype, otext in orphans:
            ovec = self._tfidf_vector(otext, idf)
            best_score = 0.03  # 最低阈值（降低以匹配短文本）
            best_target = None

            for tid, tvec in target_vectors.items():
                score = self._cosine(ovec, tvec)
                if score > best_score:
                    best_score = score
                    best_target = tid

            if best_target:
                target_type = self.target_type.get(best_target, "?")
                rel_type = "SEMANTIC_SIMILAR" if best_score > 0.2 else "WEAKLY_RELATED"
                relations.append(Relation(
                    source_id=oid, target_id=best_target,
                    relation_type=rel_type,
                    confidence=round(best_score, 2),
                    source_file="link_semantic",
                    metadata={"target_type": target_type, "score": round(best_score, 3)},
                ))

        return relations

    # ── 桌面笔记关键词桥接 ──────────────────────────

    def _link_desktop_by_keywords(self) -> List:
        """桌面笔记通过关键词子串搜索桥接到已知实体"""
        from ..kg_schema import Relation
        relations = []

        desktop_ids = [eid for eid, attrs in self.entities.items()
                       if attrs.get("entity_type") == "Guardrail"
                       and attrs.get("source") == "Desktop/1.txt"]

        if not desktop_ids:
            return relations

        # 关键词 → 实体 ID 子串（用于模糊匹配）
        kw_to_substrings = {
            # ── 地理真题 → 仅连专业术语库和自然地理论文 ──
            "侵蚀": ["土壤侵蚀", "RUSLE", "沟蚀", "USLE", "DEM", "地形"],
            "紫色土": ["土壤", "RUSLE", "紫色土", "侵蚀"],
            "地貌": ["DEM", "数字地形", "地形分析", "地貌", "侵蚀"],
            "喀斯特": ["DEM", "地形", "地貌", "侵蚀", "喀斯特"],
            "生态": ["InVEST", "生态", "植被", "生态系统"],
            "气候": ["气候", "降水", "温度"],
            "板块": ["构造", "地震", "地质"],
            "断裂": ["构造", "地震", "断层"],
            "变质": ["地质", "岩石", "变质"],
            "土壤": ["土壤", "RUSLE", "USLE", "侵蚀"],
            "纬度": ["气候", "DEM", "地带性"],
            "锋": ["气象", "气候", "天气"],
            "太阳高度角": ["DEM", "太阳", "辐射", "地形"],
            "雪线": ["气候", "DEM", "冰川", "温度"],
            "副高": ["气候", "降水", "气象", "旱涝"],
            "盐度": ["水文", "海洋"],
            "城市化": ["GIS", "空间分析", "城市", "遥感", "土地利用"],
            "工业": ["GIS", "空间分析", "经济地理"],
            "人口": ["GIS", "人口", "空间分析"],
            "旅游": ["GIS", "旅游资源", "空间分析"],
            "文化景观": ["文化", "景观"],
            "语言": ["文化", "传播"],
            # ── 考研经验 → 仅连学习方法类内容 ──
            "考研": ["毕业要求", "学位", "导师"],
            "背诵": ["刻意练习", "记忆", "学习方法"],
            "真题": ["真题"],
            "笔记": ["刻意练习", "认知觉醒"],
        }

        # 为每个关键词建立候选实体索引
        for did in desktop_ids:
            rule = self.entities[did].get("rule", "")
            seen_targets = set()

            for kw, substrings in kw_to_substrings.items():
                if kw not in rule:
                    continue
                # 在所有实体中搜索匹配子串的
                for eid, attrs in self.entities.items():
                    if eid in seen_targets or eid == did:
                        continue
                    etype = attrs.get("entity_type", "")
                    if etype not in ("Technique", "Method", "Guardrail",
                                     "ResearchDirection", "Paper", "Term"):
                        continue
                    # 检查实体 ID、label、rule、name 等是否包含子串
                    searchable = " ".join([
                        eid,
                        str(attrs.get("label", "")),
                        str(attrs.get("rule", "")),
                        str(attrs.get("name", "")),
                        str(attrs.get("canonical_name", "")),
                    ]).lower()
                    if any(s.lower() in searchable for s in substrings):
                        seen_targets.add(eid)
                        relations.append(Relation(
                            source_id=did, target_id=eid,
                            relation_type="CONCEPT_LINK",
                            confidence=0.4,
                            source_file="link_semantic_keyword",
                            metadata={"keyword": kw},
                        ))
                        if len(seen_targets) >= 5:  # 限制每个桌面笔记的连接数
                            break

        return relations

    # ── 同域/同源互连 ────────────────────────────────

    def _link_same_domain(self) -> List:
        """同 domain 的 Guardrail 互连"""
        from ..kg_schema import Relation
        relations = []
        by_domain = defaultdict(list)
        for eid, attrs in self.entities.items():
            if attrs.get("entity_type") == "Guardrail":
                domain = attrs.get("domain", "")
                if domain:
                    by_domain[domain].append(eid)
        for domain, ids in by_domain.items():
            if len(ids) < 2:
                continue
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    relations.append(Relation(
                        source_id=ids[i], target_id=ids[j],
                        relation_type="SAME_DOMAIN",
                        confidence=0.3,
                        source_file="link_semantic",
                        metadata={"domain": domain},
                    ))
        return relations

    def _link_same_source(self) -> List:
        """同 source 目录的 ResearchDirection 互连"""
        from ..kg_schema import Relation
        relations = []
        by_source = defaultdict(list)
        for eid, attrs in self.entities.items():
            if attrs.get("entity_type") == "ResearchDirection":
                src = attrs.get("source", "")
                if src:
                    # 取目录前缀
                    dir_prefix = "/".join(src.split("/")[:-1]) if "/" in src else src
                    by_source[dir_prefix].append(eid)
        for src, ids in by_source.items():
            if len(ids) < 2:
                continue
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    relations.append(Relation(
                        source_id=ids[i], target_id=ids[j],
                        relation_type="SAME_SOURCE",
                        confidence=0.3,
                        source_file="link_semantic",
                        metadata={"source": src},
                    ))
        return relations

    # ── TF-IDF 实现 ──────────────────────────────────

    def _tokenize(self, text: str) -> List[str]:
        """中英文混合分词（零依赖）"""
        tokens = []
        # 英文词
        for w in re.findall(r"[a-zA-Z]{2,}", text):
            tokens.append(w.lower())
        # 中文 2-4 字 N-gram
        chinese = re.findall(r"[一-鿿]+", text)
        for chunk in chinese:
            for n in [4, 3, 2]:
                for i in range(len(chunk) - n + 1):
                    tokens.append(chunk[i:i+n])
        # 数字和特殊标识符
        for w in re.findall(r"[A-Z]{2,8}", text):
            tokens.append(w.lower())
        return tokens

    def _compute_idf(self, docs: List[str]) -> Dict[str, float]:
        """计算 IDF"""
        N = len(docs)
        df = defaultdict(int)
        for doc in docs:
            seen = set()
            for token in self._tokenize(doc):
                if token not in seen:
                    df[token] += 1
                    seen.add(token)
        return {t: math.log((N + 1) / (df[t] + 1)) + 1 for t in df}

    def _tfidf_vector(self, text: str, idf: Dict[str, float]) -> Dict[str, float]:
        """计算 TF-IDF 向量"""
        tokens = self._tokenize(text)
        tf = defaultdict(int)
        for t in tokens:
            tf[t] += 1
        max_tf = max(tf.values()) if tf else 1
        return {t: (tf[t] / max_tf) * idf.get(t, 0) for t in tf}

    def _cosine(self, v1: Dict[str, float], v2: Dict[str, float]) -> float:
        """余弦相似度"""
        common = set(v1.keys()) & set(v2.keys())
        if not common:
            return 0.0
        dot = sum(v1[k] * v2[k] for k in common)
        norm1 = math.sqrt(sum(x * x for x in v1.values()))
        norm2 = math.sqrt(sum(x * x for x in v2.values()))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)
