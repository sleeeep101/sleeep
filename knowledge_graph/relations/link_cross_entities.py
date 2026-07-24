"""
跨实体批量关系发现
==================
1. Term → Paper: 术语出现在论文中 (INTRODUCES / USES_TERM)
2. Paper → Paper: 主题/方法共现 (SHARES_TOPIC / SHARES_METHOD)
3. Concept → Research: 概念卡片关联研究方向
4. Paper → Paper: 同源日报 (FROM_SAME_DAILY)
"""

import re
from typing import List, Dict, Set, Tuple

from ..kg_schema import Relation


class CrossEntityLinker:
    """跨实体批量关系发现"""

    def __init__(self, entities: Dict[str, Dict]):
        self.entities = entities
        self._index_by_type()

    def _index_by_type(self):
        """按类型建立索引"""
        self.papers = {eid: e for eid, e in self.entities.items()
                       if e.get("entity_type") == "Paper"}
        self.terms = {eid: e for eid, e in self.entities.items()
                      if e.get("entity_type") == "Term"}
        self.concepts = {eid: e for eid, e in self.entities.items()
                         if e.get("entity_type") == "Guardrail"
                         and e.get("domain", "").startswith("读书笔记")}

    def extract_all_relations(self) -> List[Relation]:
        """批量发现所有关系"""
        relations = []

        # 1. Term → Paper
        relations.extend(self._link_terms_to_papers())

        # 2. Paper ↔ Paper (topic co-occurrence)
        relations.extend(self._link_papers_by_topics())

        # 3. Paper ↔ Paper (same daily)
        relations.extend(self._link_papers_same_daily())

        # 4. Concept → Research (GIS/遥感 keywords)
        relations.extend(self._link_concepts_to_research())

        # 5. Reading records → Papers (match by title)
        relations.extend(self._link_reading_records_to_papers())

        # 6. Guardrails → ResearchDirection (keyword match)
        relations.extend(self._link_guardrails_to_directions())

        # 7. Techniques → Papers (source text match)
        relations.extend(self._link_techniques_to_papers())

        # 8. Book items → Book entities (ID prefix match)
        relations.extend(self._link_book_items_to_books())

        return relations

    # ── 1. Term → Paper ──────────────────────────────

    def _link_terms_to_papers(self) -> List[Relation]:
        """如果术语的英文/中文名出现在论文中，建立链接"""
        relations = []

        # 为每个术语建搜索词列表
        term_search: Dict[str, List[str]] = {}
        for tid, t in self.terms.items():
            search_words = []
            eng = t.get("english", "")
            chn = t.get("chinese", "")
            if eng:
                # 取英文名的主要单词（去括号和缩写）
                eng_clean = re.sub(r"\(.*?\)", "", eng).strip()
                search_words.append(eng_clean.lower())
                # 也加入缩写形式
                abbr_match = re.search(r"\((\w+)\)", eng)
                if abbr_match and len(abbr_match.group(1)) >= 3:
                    search_words.append(abbr_match.group(1).lower())
            if chn:
                search_words.append(chn)
            if search_words:
                term_search[tid] = search_words

        # 对每篇论文检查是否包含术语
        for pid, paper in self.papers.items():
            searchable = " ".join([
                paper.get("title", ""),
                paper.get("summary", ""),
                " ".join(paper.get("topics", [])),
                " ".join(paper.get("methods", [])),
            ]).lower()

            for tid, words in term_search.items():
                for w in words:
                    if len(w) >= 4 and w.lower() in searchable:
                        relations.append(Relation(
                            source_id=pid,
                            target_id=tid,
                            relation_type="INTRODUCES",
                            confidence=0.7,
                            source_file="link_cross_entities",
                            metadata={"matched_word": w},
                        ))
                        break  # 一个术语匹配一次就够了

        return relations

    # ── 2. Paper ↔ Paper (topic co-occurrence) ─────

    def _link_papers_by_topics(self) -> List[Relation]:
        """主题/方法共现的论文互链"""
        relations = []
        paper_topics: Dict[str, Set[str]] = {}

        for pid, paper in self.papers.items():
            topics = set(t.lower() for t in paper.get("topics", []))
            methods = set(m.lower() for m in paper.get("methods", []))
            paper_topics[pid] = topics | methods

        paper_ids = list(self.papers.keys())
        # 只在时间相近的论文间建立链接
        for i in range(len(paper_ids)):
            for j in range(i + 1, len(paper_ids)):
                pi, pj = paper_ids[i], paper_ids[j]
                ti = paper_topics.get(pi, set())
                tj = paper_topics.get(pj, set())
                if not ti or not tj:
                    continue

                overlap = ti & tj
                if len(overlap) >= 2:  # 至少共享 2 个主题/方法
                    relations.append(Relation(
                        source_id=pi,
                        target_id=pj,
                        relation_type="SHARES_TOPIC",
                        confidence=min(0.9, 0.5 + 0.1 * len(overlap)),
                        source_file="link_cross_entities",
                        metadata={"shared": list(overlap)[:5]},
                    ))

        return relations

    # ── 3. Paper ↔ Paper (same daily) ───────────────

    def _link_papers_same_daily(self) -> List[Relation]:
        """同一天日报产出的论文互链"""
        relations = []
        date_papers: Dict[str, List[str]] = {}

        for pid, paper in self.papers.items():
            kb_date = paper.get("kb_date", "")
            if kb_date:
                date_papers.setdefault(kb_date, []).append(pid)

        for date, pids in date_papers.items():
            if len(pids) < 2:
                continue
            for i in range(len(pids)):
                for j in range(i + 1, len(pids)):
                    relations.append(Relation(
                        source_id=pids[i],
                        target_id=pids[j],
                        relation_type="FROM_SAME_DAILY",
                        confidence=0.5,
                        source_file="link_cross_entities",
                        metadata={"date": date},
                    ))

        return relations

    # ── 4. Concept → Research ───────────────────────

    def _link_concepts_to_research(self) -> List[Relation]:
        """书籍概念卡片关联到研究方向"""
        relations = []
        research_keywords = [
            ("GIS", "GIS与空间分析"),
            ("遥感", "遥感"),
            ("dem", "DEM与数字地形分析"),
            ("地形", "DEM与数字地形分析"),
            ("空间分析", "GIS与空间分析"),
            ("土壤侵蚀", "土壤侵蚀与水土保持"),
            ("侵蚀", "土壤侵蚀与水土保持"),
            ("机器学习", "AI与深度学习"),
            ("深度学习", "AI与深度学习"),
            ("写作", "学术写作"),
            ("论文", "学术写作"),
        ]

        for cid, concept in self.concepts.items():
            condition = concept.get("condition", "")
            rule = concept.get("rule", "")
            searchable = (rule + " " + condition).lower()

            for kw, direction in research_keywords:
                if kw.lower() in searchable:
                    # 找到匹配的研究方向实体
                    for eid, e in self.entities.items():
                        if (e.get("entity_type") == "ResearchDirection"
                                and e.get("name", "") == direction):
                            relations.append(Relation(
                                source_id=cid,
                                target_id=eid,
                                relation_type="RELATES_TO",
                                confidence=0.5,
                                source_file="link_cross_entities",
                                metadata={"keyword": kw},
                            ))
                            break

        return relations

    # ── 5. Reading records → Papers ──────────────────

    def _link_reading_records_to_papers(self) -> List[Relation]:
        """已读清单记录匹配到论文实体"""
        relations = []
        reading_records = {eid: e for eid, e in self.entities.items()
                           if e.get("entity_type") == "DailyReport"
                           and e.get("report_type") == "reading_record"}

        for rid, record in reading_records.items():
            record_title = record.get("summary", "")
            if len(record_title) < 10:
                continue
            for pid, paper in self.papers.items():
                paper_title = paper.get("title", "")
                if (len(paper_title) > 10
                        and paper_title[:30].lower() in record_title.lower()):
                    relations.append(Relation(
                        source_id=rid, target_id=pid,
                        relation_type="RECORDS",
                        confidence=0.8,
                        source_file="link_cross_entities",
                    ))
                    break
        return relations

    # ── 6. Guardrails → ResearchDirection ───────────

    def _link_guardrails_to_directions(self) -> List[Relation]:
        """规则实体通过关键词关联到研究方向"""
        relations = []
        directions = {eid: e for eid, e in self.entities.items()
                      if e.get("entity_type") == "ResearchDirection"}
        guardrails = {eid: e for eid, e in self.entities.items()
                      if e.get("entity_type") == "Guardrail"}

        for gid, guard in guardrails.items():
            searchable = (guard.get("rule", "") + " " +
                          guard.get("domain", "") + " " +
                          guard.get("condition", "")).lower()
            for did, direction in directions.items():
                dname = direction.get("name", "").lower()
                if dname and len(dname) > 2 and dname in searchable:
                    relations.append(Relation(
                        source_id=gid, target_id=did,
                        relation_type="GOVERNED_BY",
                        confidence=0.4,
                        source_file="link_cross_entities",
                    ))
                    break
        return relations

    # ── 7. Techniques → Papers ─────────────────────

    def _link_techniques_to_papers(self) -> List[Relation]:
        """方法卡片/论文索引关联到学术论文"""
        relations = []
        techniques = {eid: e for eid, e in self.entities.items()
                      if e.get("entity_type") == "Technique"
                      and e.get("category") in ("PaperIndex", "MethodCard")}

        for tid, tech in techniques.items():
            sources = tech.get("sources", [])
            template = tech.get("template", "")
            searchable = (template + " " + " ".join(sources)).lower()
            for pid, paper in self.papers.items():
                authors = paper.get("authors", "").lower()
                title = paper.get("title", "").lower()
                if (len(authors) > 5 and authors[:20] in searchable) or \
                   (len(title) > 10 and title[:40] in searchable):
                    relations.append(Relation(
                        source_id=tid, target_id=pid,
                        relation_type="DERIVED_FROM",
                        confidence=0.6,
                        source_file="link_cross_entities",
                    ))
                    break
        return relations

    # ── 8. Book items → Book entities ────────────────

    def _link_book_items_to_books(self) -> List[Relation]:
        """书籍的 Technique/Guardrail 通过 ID 前缀关联到 Book"""
        relations = []
        books = {eid: e for eid, e in self.entities.items()
                 if e.get("entity_type") == "ResearchDirection"
                 and eid.startswith("book_")}
        book_items = {eid: e for eid, e in self.entities.items()
                      if (e.get("entity_type") in ("Technique", "Guardrail"))
                      and (eid.startswith("action_") or eid.startswith("quote_")
                           or eid.startswith("transfer_") or eid.startswith("concept_"))}

        for iid, item in book_items.items():
            # 从 ID 提取 book_slug
            parts = iid.split("_", 2)
            if len(parts) >= 2:
                slug = parts[1]
                for bid in books:
                    if slug in bid:
                        relations.append(Relation(
                            source_id=iid, target_id=bid,
                            relation_type="BELONGS_TO",
                            confidence=0.9,
                            source_file="link_cross_entities",
                        ))
                        break
        return relations
