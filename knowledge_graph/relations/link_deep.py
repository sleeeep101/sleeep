"""
深度关系发现 — 精准打击孤立体
============================
1. Term → Paper: 中文分词级匹配 + 语境关键词提取
2. ReadingRecord → DailyReport: 按日期关联
3. Term ↔ Term: 同分类互连 + 关联术语引用
"""

import re
from typing import List, Dict, Set

from ..kg_schema import Relation
from ..kg_config import TERM_CATEGORY_MAP


class DeepLinker:
    """深度关系发现"""

    def __init__(self, entities: Dict[str, Dict]):
        self.entities = entities
        self._index()

    def _index(self):
        self.papers = {eid: e for eid, e in self.entities.items()
                       if e.get("entity_type") == "Paper"}
        self.terms = {eid: e for eid, e in self.entities.items()
                      if e.get("entity_type") == "Term"}
        self.daily_reports = {eid: e for eid, e in self.entities.items()
                              if e.get("entity_type") == "DailyReport"}

    def extract_all(self) -> List[Relation]:
        relations = []
        relations.extend(self._deep_term_paper())
        relations.extend(self._reading_to_daily())
        relations.extend(self._term_to_term())
        return relations

    # ── 1. Term → Paper (深度中文匹配) ──────────────

    def _deep_term_paper(self) -> List[Relation]:
        """改进术语匹配：提取中文关键词 + 放宽阈值"""
        relations = []

        # 获取已连接的 term（避免重复）
        existing = set()
        for r in relations:
            if r.relation_type == "INTRODUCES":
                existing.add((r.source_id, r.target_id))

        # 为每个术语提取搜索词
        for tid, term in self.terms.items():
            search_words = set()

            # 英文名的主要单词
            eng = term.get("english", "")
            for w in re.findall(r"[a-zA-Z]{3,}", eng):
                search_words.add(w.lower())

            # 中文名 + 拆分为 2-4 字的关键片段
            chn = term.get("chinese", "")
            search_words.add(chn)
            # 提取中文中 2-4 字的连续片段
            chn_clean = re.sub(r"[（）()].*?[）)]", "", chn)
            for seg in self._segment_chinese(chn_clean):
                if len(seg) >= 2:
                    search_words.add(seg)

            # 语境中的英文缩写
            ctx = term.get("explanation", "")
            for w in re.findall(r"[A-Z]{2,6}", ctx):
                search_words.add(w.lower())
            for w in re.findall(r"[a-z]{4,}", ctx):
                search_words.add(w.lower())

            # 在论文中搜索
            for pid, paper in self.papers.items():
                if (pid, tid) in existing:
                    continue

                searchable = " ".join([
                    paper.get("title", ""),
                    paper.get("summary", ""),
                    " ".join(paper.get("topics", [])),
                    " ".join(paper.get("methods", [])),
                ]).lower()

                matches = 0
                matched = []
                for w in search_words:
                    if len(w) >= 2 and w.lower() in searchable:
                        matches += 1
                        matched.append(w)

                # 至少匹配 2 个不同的词，或一个 4 字以上中文词
                if matches >= 2 or (matches >= 1 and any(len(m) >= 4 for m in matched)):
                    relations.append(Relation(
                        source_id=pid, target_id=tid,
                        relation_type="INTRODUCES",
                        confidence=min(0.9, 0.4 + 0.1 * matches),
                        source_file="link_deep",
                        metadata={"matched": matched[:5]},
                    ))
                    existing.add((pid, tid))

        return relations

    def _segment_chinese(self, text: str) -> List[str]:
        """简单的中文 N-gram 分词（2/3/4 字）"""
        # 只保留中文字符
        chinese_chars = re.findall(r"[一-鿿]+", text)
        words = []
        for chunk in chinese_chars:
            for n in [4, 3, 2]:
                for i in range(len(chunk) - n + 1):
                    words.append(chunk[i:i+n])
        return words

    # ── 2. ReadingRecord → DailyReport (日期匹配) ──

    def _reading_to_daily(self) -> List[Relation]:
        """已读清单记录按日期关联到论文阅读日报"""
        relations = []

        reading_records = {eid: e for eid, e in self.daily_reports.items()
                           if e.get("report_type") == "reading_record"}
        paper_dailies = {eid: e for eid, e in self.daily_reports.items()
                         if e.get("report_type") == "paper_reading"}

        # 按日期索引日报
        daily_by_date: Dict[str, str] = {}
        for did, daily in paper_dailies.items():
            date = daily.get("date", "")
            if date:
                daily_by_date[date] = did

        for rid, record in reading_records.items():
            date = record.get("date", "")
            if date in daily_by_date:
                relations.append(Relation(
                    source_id=rid, target_id=daily_by_date[date],
                    relation_type="FROM_DAILY",
                    confidence=0.7,
                    source_file="link_deep",
                    metadata={"date": date},
                ))

        return relations

    # ── 3. Term ↔ Term (同分类互连) ────────────────

    def _term_to_term(self) -> List[Relation]:
        """同分类术语互连 + 显式关联引用"""
        relations = []

        # 按分类分组
        by_category: Dict[str, List[str]] = {}
        for tid, term in self.terms.items():
            cat = term.get("category", "Z")
            by_category.setdefault(cat, []).append(tid)

        # 同分类互连
        for cat, term_ids in by_category.items():
            if len(term_ids) < 2:
                continue
            for i in range(len(term_ids)):
                for j in range(i + 1, len(term_ids)):
                    relations.append(Relation(
                        source_id=term_ids[i], target_id=term_ids[j],
                        relation_type="RELATED_TO",
                        confidence=0.3,
                        source_file="link_deep",
                        metadata={"category": cat},
                    ))

        # 显式关联引用（专业术语库中的 "区别于A-039" 等）
        for tid, term in self.terms.items():
            related = term.get("related_terms", [])
            for ref_id in related:
                if ref_id in self.terms:
                    relations.append(Relation(
                        source_id=tid, target_id=ref_id,
                        relation_type="RELATED_TO",
                        confidence=0.8,
                        source_file="link_deep",
                        metadata={"explicit": True},
                    ))

        return relations
