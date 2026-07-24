"""
知识图谱构建器
=============
将提取的实体加载为 NetworkX MultiDiGraph，
添加关系，序列化为 JSON。
"""

import json
import os
import re
from typing import List, Dict, Any, Optional, Tuple

import networkx as nx

from ..kg_config import KG_DATA_FILE, ENTITY_COLORS, ACADEMIC_ROOT
from ..kg_schema import (
    Paper, Term, Technique, Innovation, DailyReport,
    Method, Concept, Guardrail, Script, ResearchDirection,
    Relation, ENTITY_CLASS_MAP,
)
from ..extractors.extract_papers import PaperExtractor
from ..extractors.extract_terms import TermExtractor
from ..extractors.extract_techniques import TechniqueExtractor
from ..extractors.extract_daily_reports import DailyReportExtractor
from ..extractors.extract_personal_brain import PersonalBrainExtractor
from ..extractors.extract_academic_workflow import AcademicWorkflowExtractor
from ..extractors.extract_reading_list import ReadingListExtractor
from ..extractors.extract_desktop_notes import DesktopNotesExtractor
from ..extractors.extract_contacts import ContactsExtractor


class KnowledgeGraphBuilder:
    """知识图谱构建器"""

    def __init__(self, kg_file: str = KG_DATA_FILE, *, include_private_sources: bool = False):
        """Create a builder with private local sources disabled by default."""
        self.kg_file = kg_file
        self.include_private_sources = include_private_sources
        self.graph = nx.MultiDiGraph()
        self.entities: Dict[str, Dict[str, Any]] = {}  # node_id → attributes
        self.relations: List[Relation] = []

    # ── 构建 ──────────────────────────────────────────

    def build_full(self) -> nx.MultiDiGraph:
        """全量构建知识图谱"""
        print("[KG] 开始全量构建知识图谱...")

        # Phase 1: 提取实体
        self._extract_all()

        # Phase 1.5: 跨源去重
        self._dedup()

        # Phase 2: 发现关系
        self._link_all()

        # Phase 3: 构建 NetworkX 图
        self._build_graph()

        print(f"[KG] 构建完成: {self.graph.number_of_nodes()} 节点, "
              f"{self.graph.number_of_edges()} 边")

        # Phase 4: 健康检查
        try:
            from ..kg_health import HealthMonitor
            monitor = HealthMonitor(self.graph, self.entities, self.kg_file)
            monitor.print_report()
        except Exception as exc:
            print(f"  [KG] 健康检查失败: {exc}")

        return self.graph

    def _extract_all(self) -> None:
        """提取所有实体"""
        extractors = [
            ("论文笔记", PaperExtractor()),
            ("专业术语", TermExtractor()),
            ("写作技法", TechniqueExtractor()),
            ("日报", DailyReportExtractor()),
        ]

        for name, extractor in extractors:
            try:
                entities = extractor.extract()
                for e in entities:
                    self.entities[e.id] = e.to_dict()
                print(f"  [KG] {name}: {len(entities)} 条")
            except Exception as exc:
                print(f"  [KG] {name} 提取失败: {exc}")

        # 创新点（Phase 2）
        try:
            from ..relations.link_innovation import InnovationLinker
            linker = InnovationLinker()
            innovations = linker.extract_innovations()
            for e in innovations:
                self.entities[e.id] = e.to_dict()
            print(f"  [KG] 创新点: {len(innovations)} 条")
        except Exception as exc:
            print(f"  [KG] 创新点提取失败: {exc}")

        # Personal-Brain
        try:
            pb_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))), "..", "Personal-Brain")
            pb_root = os.path.normpath(pb_root)
            if os.path.isdir(pb_root) and self.include_private_sources:
                pb_ext = PersonalBrainExtractor(pb_root)
                pb_entities = pb_ext.extract()
                for e in pb_entities:
                    self.entities[e.id] = e.to_dict()
                types = {}
                for e in pb_entities:
                    t = getattr(e, "entity_type", "Unknown")
                    types[t] = types.get(t, 0) + 1
                summary = ", ".join(f"{k}:{v}" for k, v in types.items())
                print(f"  [KG] Personal-Brain: {len(pb_entities)} 条 ({summary})")
        except Exception as exc:
            print(f"  [KG] Personal-Brain 提取失败: {exc}")

        # academic-workflow 全目录
        try:
            aw_ext = AcademicWorkflowExtractor(ACADEMIC_ROOT)
            aw_entities = aw_ext.extract()
            for e in aw_entities:
                self.entities[e.id] = e.to_dict()
            types = {}
            for e in aw_entities:
                t = getattr(e, "entity_type", "Unknown")
                types[t] = types.get(t, 0) + 1
            summary = ", ".join(f"{k}:{v}" for k, v in types.items())
            print(f"  [KG] academic-workflow全目录: {len(aw_entities)} 条 ({summary})")
        except Exception as exc:
            print(f"  [KG] academic-workflow全目录提取失败: {exc}")

        # 已读论文清单
        try:
            rl_ext = ReadingListExtractor(ACADEMIC_ROOT)
            rl_entities = rl_ext.extract()
            for e in rl_entities:
                self.entities[e.id] = e.to_dict()
            print(f"  [KG] 已读论文清单: {len(rl_entities)} 条")
        except Exception as exc:
            print(f"  [KG] 已读清单提取失败: {exc}")

        # 桌面笔记（个人原则 + 历史）
        if not self.include_private_sources:
            print("  [KG] Private sources skipped (use explicit opt-in to include them).")
            return

        desktop_notes = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Desktop", "1.txt")
        if os.path.exists(desktop_notes):
            try:
                dn_ext = DesktopNotesExtractor(desktop_notes)
                dn_entities = dn_ext.extract()
                for e in dn_entities:
                    self.entities[e.id] = e.to_dict()
                print(f"  [KG] 桌面笔记: {len(dn_entities)} 条")
            except Exception as exc:
                print(f"  [KG] 桌面笔记提取失败: {exc}")
        # 人脉联系人
        contacts_file = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Desktop", "人脉.txt")
        if os.path.exists(contacts_file):
            try:
                ct_ext = ContactsExtractor(contacts_file)
                ct_entities = ct_ext.extract()
                for e in ct_entities:
                    self.entities[e.id] = e.to_dict()
                print(f"  [KG] 人脉联系人: {len(ct_entities)} 条")
            except Exception as exc:
                print(f"  [KG] 人脉提取失败: {exc}")


    def _dedup(self) -> None:
        """跨源去重：合并同义实体，保留信息最丰富的版本"""
        removed = 0
        seen = {}  # (entity_type, normalized_key) -> (best_id, char_count)

        for eid in sorted(self.entities.keys()):
            attrs = self.entities[eid]
            etype = attrs.get("entity_type", "")
            label = str(attrs.get("label", ""))
            # 生成归一化 key
            key = self._dedup_key(etype, attrs)
            if not key:
                continue

            if key in seen:
                best_id, best_chars = seen[key]
                current_chars = len(json.dumps(attrs, ensure_ascii=False))
                if current_chars > best_chars:
                    # 当前版本信息更丰富，替换
                    del self.entities[best_id]
                    seen[key] = (eid, current_chars)
                    removed += 1
                else:
                    del self.entities[eid]
                    removed += 1
            else:
                seen[key] = (eid, len(json.dumps(attrs, ensure_ascii=False)))

        if removed:
            print(f"  [KG] 去重: {removed} 个重复实体已合并")

    def _dedup_key(self, etype: str, attrs: Dict) -> str:
        """生成去重用的归一化 key"""
        if etype == "Paper":
            return "paper:" + attrs.get("title", "")[:60].lower().strip()
        if etype == "Term":
            eng = attrs.get("english", "").lower().strip()
            return f"term:{eng}" if eng else None
        if etype == "Technique":
            return "tech:" + attrs.get("name", "")[:60].lower().strip()
        if etype == "Guardrail":
            return "rule:" + attrs.get("rule", "")[:80].lower().strip()
        if etype == "DailyReport":
            return "daily:" + attrs.get("id", "")
        return None

    def _link_all(self) -> None:
        """发现所有关系"""
        self._link_basic()
        self._link_innovations()
        self._link_paper_methods()
        self._link_cross_entities()
        self._link_deep()
        self._link_semantic()

    def _link_basic(self) -> None:
        """基础关系发现"""
        # 1. 技法 → 论文（通过来源字段匹配）
        tech_entities = [e for eid, e in self.entities.items()
                         if e.get("entity_type") == "Technique"]
        paper_entities = {eid: e for eid, e in self.entities.items()
                          if e.get("entity_type") == "Paper"}

        for tech_e in tech_entities:
            sources = tech_e.get("sources", [])
            for src in sources:
                # 匹配作者名 + 年份 在论文标题中出现
                for pid, paper in paper_entities.items():
                    title = paper.get("title", "")
                    authors = paper.get("authors", "")
                    # 简单字符串匹配
                    src_parts = src.replace("(", "").replace(")", "").split()
                    if len(src_parts) >= 1:
                        for part in src_parts:
                            if len(part) > 2 and (part in title or part in authors):
                                self.relations.append(Relation(
                                    source_id=tech_e["id"],
                                    target_id=pid,
                                    relation_type="DERIVED_FROM",
                                    confidence=0.7,
                                    source_file="link_basic",
                                    metadata={"source_text": src},
                                ))
                                break

        # 2. 日报 → 论文（通过日期匹配）
        daily_entities = [e for eid, e in self.entities.items()
                          if e.get("entity_type") == "DailyReport"
                          and e.get("report_type") == "paper_reading"]
        for daily in daily_entities:
            daily_date = daily.get("date", "")
            for pid, paper in paper_entities.items():
                kb_date = paper.get("kb_date", "")
                if kb_date == daily_date:
                    self.relations.append(Relation(
                        source_id=daily["id"],
                        target_id=pid,
                        relation_type="GENERATED",
                        confidence=0.9,
                        source_file="link_basic",
                    ))

    def _link_innovations(self) -> None:
        """Innovation → Paper + DailyReport 关系"""
        try:
            from ..relations.link_innovation import InnovationLinker
            innov_ids = [eid for eid, e in self.entities.items()
                         if e.get("entity_type") == "Innovation"]
            if not innov_ids:
                return
            innovations = []
            for iid in innov_ids:
                attrs = self.entities[iid]
                innovations.append(Innovation(
                    id=attrs["id"],
                    innovation_type=attrs.get("innovation_type", ""),
                    description=attrs.get("description", ""),
                    source_paper=attrs.get("source_paper", ""),
                    source_daily_report=attrs.get("source_daily_report", ""),
                    source_kb=attrs.get("source_kb", ""),
                    direction=attrs.get("direction", ""),
                    suitable_for=attrs.get("suitable_for", ""),
                    credibility=attrs.get("credibility", ""),
                    status=attrs.get("status", ""),
                ))
            linker = InnovationLinker()
            innov_relations = linker.extract_relations(innovations)
            self.relations.extend(innov_relations)
        except Exception:
            pass

    def _link_paper_methods(self) -> None:
        """Paper → Method 关系"""
        try:
            from ..relations.link_paper_method import PaperMethodLinker

            paper_ids = [eid for eid, e in self.entities.items()
                         if e.get("entity_type") == "Paper"]
            if not paper_ids:
                return

            papers = []
            for pid in paper_ids:
                attrs = self.entities[pid]
                papers.append(Paper(
                    id=attrs["id"], title=attrs.get("title", ""),
                    topics=attrs.get("topics", []),
                    methods=attrs.get("methods", []),
                    summary=attrs.get("summary", ""),
                ))

            linker = PaperMethodLinker()
            methods = linker.extract_methods_from_papers(papers)

            # 添加 Method 实体
            for m in methods:
                if m.id not in self.entities:
                    self.entities[m.id] = m.to_dict()

            # 添加关系
            rels = linker.build_relations(papers, methods)
            self.relations.extend(rels)

            print(f"  [KG] 方法实体: {len(methods)} 条, "
                  f"USES_METHOD 关系: {len(rels)} 条")
        except Exception as exc:
            print(f"  [KG] 方法关系提取失败: {exc}")

    def _link_cross_entities(self) -> None:
        """跨实体批量关系发现"""
        try:
            from ..relations.link_cross_entities import CrossEntityLinker
            linker = CrossEntityLinker(self.entities)
            cross_rels = linker.extract_all_relations()
            self.relations.extend(cross_rels)

            # 统计关系类型
            type_counts = {}
            for r in cross_rels:
                type_counts[r.relation_type] = type_counts.get(r.relation_type, 0) + 1
            summary = ", ".join(f"{k}:{v}" for k, v in sorted(type_counts.items()))
            print(f"  [KG] 跨实体关系: {len(cross_rels)} 条 ({summary})")
        except Exception as exc:
            print(f"  [KG] 跨实体关系提取失败: {exc}")

    def _link_deep(self) -> None:
        """深度关系发现（Term 中文匹配 + 日期关联 + 术语互连）"""
        try:
            from ..relations.link_deep import DeepLinker
            linker = DeepLinker(self.entities)
            deep_rels = linker.extract_all()
            self.relations.extend(deep_rels)
            type_counts = {}
            for r in deep_rels:
                type_counts[r.relation_type] = type_counts.get(r.relation_type, 0) + 1
            summary = ", ".join(f"{k}:{v}" for k, v in sorted(type_counts.items()))
            print(f"  [KG] 深度关系: {len(deep_rels)} 条 ({summary})")
        except Exception as exc:
            print(f"  [KG] 深度关系提取失败: {exc}")

    def _link_semantic(self) -> None:
        """零依赖语义相似度连接孤立体"""
        try:
            from ..relations.link_semantic import SemanticLinker
            linker = SemanticLinker(self.entities)
            sem_rels = linker.extract_all()
            self.relations.extend(sem_rels)
            type_counts = {}
            for r in sem_rels:
                type_counts[r.relation_type] = type_counts.get(r.relation_type, 0) + 1
            summary = ", ".join(f"{k}:{v}" for k, v in sorted(type_counts.items()))
            print(f"  [KG] 语义连接: {len(sem_rels)} 条 ({summary})")
        except Exception as exc:
            print(f"  [KG] 语义连接失败: {exc}")

    def _build_graph(self) -> None:
        """将实体和关系填充到 NetworkX 图"""
        self.graph = nx.MultiDiGraph()

        # 添加节点
        for node_id, attrs in self.entities.items():
            etype = attrs.get("entity_type", "Unknown")
            node_data = dict(attrs)  # copy
            node_data.setdefault("label", node_id)
            node_data.setdefault("color", ENTITY_COLORS.get(etype, "#999999"))
            self.graph.add_node(node_id, **node_data)

        # 添加边
        for rel in self.relations:
            if rel.source_id in self.graph and rel.target_id in self.graph:
                self.graph.add_edge(
                    rel.source_id, rel.target_id,
                    key=rel.relation_type,
                    type=rel.relation_type,
                    confidence=rel.confidence,
                    source_file=rel.source_file,
                    **rel.metadata,
                )

    # ── 序列化 ────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """将当前图谱状态序列化为字典"""
        # 节点
        nodes = []
        for node_id, attrs in self.graph.nodes(data=True):
            node_data = {"id": node_id, **attrs}
            nodes.append(node_data)

        # 边
        edges = []
        for u, v, key, data in self.graph.edges(keys=True, data=True):
            edge_data = {"source": u, "target": v, "key": key, **data}
            edges.append(edge_data)

        return {"nodes": nodes, "edges": edges}

    def save(self, filepath: Optional[str] = None) -> str:
        """保存图为 JSON"""
        target = filepath or self.kg_file
        data = self.to_dict()
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[KG] 图谱已保存到 {target}")
        return target

    @classmethod
    def load(cls, filepath: Optional[str] = None) -> "KnowledgeGraphBuilder":
        """从 JSON 加载图"""
        graph_path = filepath or KG_DATA_FILE
        builder = cls(kg_file=graph_path)

        if not os.path.exists(graph_path):
            print(f"[KG] 图谱文件 {graph_path} 不存在，返回空图")
            return builder

        with open(graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        builder.graph = nx.MultiDiGraph()
        for node_data in data.get("nodes", []):
            node = dict(node_data)
            node_id = node.pop("id")
            builder.graph.add_node(node_id, **node)
            builder.entities[node_id] = node

        for edge_data in data.get("edges", []):
            edge = dict(edge_data)
            source = edge.pop("source")
            target = edge.pop("target")
            key = edge.pop("key", None)
            builder.graph.add_edge(source, target, key=key, **edge)
            builder.relations.append(Relation(
                source_id=source, target_id=target,
                relation_type=edge.get("type", ""),
                confidence=edge.get("confidence", 1.0),
                source_file=edge.get("source_file", ""),
            ))

        print(f"[KG] 从 {graph_path} 加载图谱: "
              f"{builder.graph.number_of_nodes()} 节点, "
              f"{builder.graph.number_of_edges()} 边")
        return builder

    # ── 统计 ──────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        """返回图谱统计信息"""
        if self.graph.number_of_nodes() == 0:
            return {"nodes": 0, "edges": 0}

        type_counts = {}
        for _, attrs in self.graph.nodes(data=True):
            etype = attrs.get("entity_type", "Unknown")
            type_counts[etype] = type_counts.get(etype, 0) + 1

        edge_type_counts = {}
        for _, _, _, data in self.graph.edges(keys=True, data=True):
            etype = data.get("type", "Unknown")
            edge_type_counts[etype] = edge_type_counts.get(etype, 0) + 1

        # 连通分量
        if self.graph.is_directed():
            components = list(nx.weakly_connected_components(self.graph))
        else:
            components = list(nx.connected_components(self.graph))

        # 孤立节点
        isolated = [n for n in self.graph.nodes()
                    if self.graph.degree(n) == 0]

        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "entity_type_counts": type_counts,
            "edge_type_counts": edge_type_counts,
            "connected_components": len(components),
            "largest_component_size": max(len(c) for c in components) if components else 0,
            "isolated_nodes": len(isolated),
            "isolated_ratio": len(isolated) / max(self.graph.number_of_nodes(), 1),
        }
