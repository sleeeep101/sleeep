"""
长期知识库.md → Paper 实体提取器
================================
解析 KB-YYYY-MM-DD-NN 和 Paper_ID: YYYY-MM-DD_FNN 两种格式。
"""

import re
import os
from typing import List, Dict, Optional
from datetime import datetime

from .base import BaseExtractor, parse_fields
from ..kg_config import (
    KB_HEADER_PATTERN, PAPER_ID_HEADER_PATTERN, LONG_TERM_KB, KG_HASH_CACHE,
    METHOD_KEYWORDS,
)
from ..kg_schema import Paper


class PaperExtractor(BaseExtractor):
    """长期知识库论文提取器"""

    def __init__(self):
        super().__init__(LONG_TERM_KB, KG_HASH_CACHE)

    def extract(self) -> List[Paper]:
        if not os.path.exists(self.source_path):
            return []

        papers: List[Paper] = []
        seen_ids: set = set()

        with open(self.source_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 找所有 ### KB- 和 ### Paper_ID: header 的位置
        header_pattern = re.compile(
            r"^###\s+((?:KB-\d{4}-\d{2}-\d{2}-\d{2,3})|(?:Paper_ID:\s*\d{4}-\d{2}-\d{2}_F\d{2,3}))",
            re.MULTILINE
        )
        header_matches = list(header_pattern.finditer(content))

        # 找该 header 之前的最近 ## YYYY-MM-DD 日期
        def find_date_before(pos: int) -> str:
            date_match = None
            for dm in re.finditer(r"^##\s+(\d{4}-\d{2}-\d{2})", content[:pos], re.MULTILINE):
                date_match = dm
            return date_match.group(1) if date_match else ""

        for i, hm in enumerate(header_matches):
            header_text = hm.group(0).strip()
            header_pos = hm.start()
            kb_date = find_date_before(header_pos)

            # 确定 block 结束位置（下一个 ### header 或 ## section 或 EOF）
            if i + 1 < len(header_matches):
                block_end = header_matches[i + 1].start()
            else:
                # 找下一个 ## section
                next_section = re.search(r"^##\s+", content[header_pos+10:], re.MULTILINE)
                if next_section:
                    block_end = header_pos + 10 + next_section.start()
                else:
                    block_end = len(content)

            block = content[header_pos:block_end]

            # ── 匹配 KB- 格式 ──
            kb_match = re.match(KB_HEADER_PATTERN, block.strip())
            if kb_match:
                paper_id = kb_match.group(1)
                title = kb_match.group(2).strip()
                if paper_id not in seen_ids:
                    seen_ids.add(paper_id)
                    paper = self._parse_kb_format(paper_id, title, block, kb_date)
                    papers.append(paper)
                continue

            # ── 匹配 Paper_ID 格式 ──
            pid_match = re.match(PAPER_ID_HEADER_PATTERN, block.strip())
            if pid_match:
                paper_id_raw = pid_match.group(1)
                paper_id = f"Paper_ID: {paper_id_raw}"
                if paper_id not in seen_ids:
                    seen_ids.add(paper_id)
                    # 从 header 行提取标题
                    header_line = block.strip().split("\n")[0]
                    title = ""
                    if "|" in header_line:
                        title = header_line.split("|", 1)[-1].strip()
                    elif "｜" in header_line:
                        title = header_line.split("｜", 1)[-1].strip()
                    paper = self._parse_paperid_format(paper_id, block, kb_date)
                    if title and not paper.title:
                        paper.title = title
                    papers.append(paper)
                continue

        return papers

    def _parse_kb_format(self, paper_id: str, title: str, block: str, kb_date: str) -> Paper:
        """解析 KB-YYYY-MM-DD-NN 格式"""
        fields = parse_fields(block)

        # 解析作者
        authors = fields.get("作者", "")

        # 解析年份
        year = None
        year_str = fields.get("年份", "")
        if year_str:
            try:
                year = int(re.search(r"\d{4}", year_str).group())
            except (ValueError, AttributeError):
                pass

        # 解析来源
        source = fields.get("来源", "") or fields.get("DOI", "")

        # 解析 DOI
        doi = fields.get("DOI", "")

        # 解析评分
        score = None
        score_str = fields.get("正式学术评分 / 100", "") or fields.get("评分", "")
        if score_str:
            try:
                score = int(re.search(r"\d+", score_str).group())
            except (ValueError, AttributeError):
                pass

        # 解析等级
        grade = fields.get("总评等级", "") or fields.get("等级", "")

        # 解析主题标签
        topics_raw = fields.get("主题标签", "") or fields.get("主题", "")
        topics = [t.strip() for t in re.split(r"[;；,，]", topics_raw) if t.strip()]

        # 解析一句话总结
        summary = fields.get("一句话总结", "") or fields.get("一句话", "")

        # 解析方法
        methods_raw = fields.get("方法", "")
        methods = [m.strip() for m in re.split(r"[;；,，]", methods_raw) if m.strip()]

        # 解析迁移价值
        transferability = fields.get("可迁移到GIS的点", "") or fields.get("迁移", "")

        # 解析可信度
        credibility = fields.get("可信度", "")

        # 解析全文状态
        reading_level = fields.get("全文证据状态", "")

        # 解析加入理由
        reason = fields.get("加入理由", "") or fields.get("加入", "")

        # ── 全文背诵：完整 block 内容 ──
        block_content = block.strip()

        # ── 解析 note.md 路径 ──
        note_path = self._resolve_note_path(title, authors, kb_date)

        return Paper(
            id=paper_id,
            title=title,
            authors=authors,
            year=year,
            source=source,
            doi=doi,
            score=score,
            grade=grade,
            topics=topics,
            summary=summary,
            methods=methods,
            transferability=transferability,
            credibility=credibility,
            reading_level=reading_level,
            block_content=block_content,
            note_path=note_path,
            kb_date=kb_date,
            reason=reason,
        )

    def _resolve_note_path(self, title: str, authors: str, kb_date: str) -> str:
        """根据论文标题/作者，扫描 paper_sources 寻找对应的 note.md"""
        paper_sources = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "01_读_论文阅读与复盘", "02_论文阅读库", "paper_sources"
        )
        if not os.path.isdir(paper_sources):
            return ""

        # 关键词：取标题前三个有意义的词
        title_words = re.findall(r"[A-Za-z一-鿿]{3,}", title)
        keywords = [w.lower() for w in title_words[:4]]

        # 作者姓氏
        if authors:
            first_author = authors.split(",")[0].split(" ")[-1].strip()
            if len(first_author) >= 3:
                keywords.insert(0, first_author.lower().replace(" ", "_"))

        best_match = ""
        best_score = 0

        for dirpath, dirnames, filenames in os.walk(paper_sources):
            for fname in filenames:
                if fname == "note.md":
                    fpath = os.path.join(dirpath, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            note_title_line = f.readline().strip("# \n")
                    except Exception:
                        continue

                    # 匹配评分
                    score = 0
                    note_lower = note_title_line.lower()
                    for kw in keywords:
                        if kw in note_lower:
                            score += 1
                    if score > best_score:
                        best_score = score
                        best_match = fpath

        # 至少匹配 2 个关键词才认为匹配成功
        if best_score >= 2:
            return best_match
        return "" if best_score < 1 else best_match

    def _parse_paperid_format(self, paper_id: str, block: str, kb_date: str) -> Paper:
        """解析 Paper_ID: YYYY-MM-DD_FNN 格式（旧格式，字段较少）"""
        fields = parse_fields(block)

        # 标题：取 header 行后的第一行非空文本
        lines = block.strip().split("\n")
        title = ""
        in_header = False
        for line in lines:
            if line.startswith("###"):
                # header 行本身可能包含标题
                if "|" in line:
                    title = line.split("|", 1)[-1].strip()
                in_header = True
                continue
            if in_header and line.strip() and not line.strip().startswith("-"):
                title = line.strip()
                break

        if not title:
            title = fields.get("标题", paper_id)

        score = None
        score_str = fields.get("正式学术评分 / 100", "")
        if score_str:
            try:
                score = int(re.search(r"\d+", score_str).group())
            except (ValueError, AttributeError):
                pass

        topics_raw = fields.get("主题标签", "")
        topics = [t.strip() for t in re.split(r"[;；,，]", topics_raw) if t.strip()]

        return Paper(
            id=paper_id,
            title=title,
            authors=fields.get("作者", ""),
            source=fields.get("来源", ""),
            score=score,
            grade=fields.get("总评等级", ""),
            topics=topics,
            summary=fields.get("一句话总结", ""),
            methods=[],
            credibility=fields.get("可信度", ""),
            reading_level=fields.get("全文证据状态", ""),
            block_content=block.strip(),
            kb_date=kb_date,
        )
