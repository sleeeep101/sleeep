"""
创新点关系提取
=============
解析可能的创新点.md 中的 wiki-link，建立 Innovation → Paper + DailyReport 的三向链接。
"""

import re
import os
from typing import List

from ..kg_config import INNOVATION_DB, INNOVATION_HEADER_PATTERN
from ..kg_schema import Innovation, Relation
from ..extractors.base import parse_fields, extract_wiki_links, parse_wiki_kb_ref, parse_wiki_daily_ref


class InnovationLinker:
    """从创新点文件提取关系"""

    def __init__(self):
        self.source_path = INNOVATION_DB

    def extract_innovations(self) -> List[Innovation]:
        """提取创新点实体"""
        if not os.path.exists(self.source_path):
            return []

        innovations = []
        with open(self.source_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 按 ### INNO- header 拆分
        for m in re.finditer(r"^###\s+(INNO-\d{4}-\d{2}-\d{2}-\d{2,3})", content, re.MULTILINE):
            inno_id = m.group(1)
            inno_start = m.start()

            # 找下一个 INNO header 或 ## section 作为结束
            next_inno = re.search(r"^###\s+INNO-", content[inno_start + 10:], re.MULTILINE)
            if next_inno:
                inno_end = inno_start + 10 + next_inno.start()
            else:
                # 找下一个 ## section
                next_section = re.search(r"^##\s+", content[inno_start + 10:], re.MULTILINE)
                if next_section:
                    inno_end = inno_start + 10 + next_section.start()
                else:
                    inno_end = min(len(content), inno_start + 2000)

            block = content[inno_start:inno_end]
            fields = parse_fields(block)

            # 提取 wiki-links
            wiki_links = extract_wiki_links(block)

            source_daily = ""
            source_kb = ""
            for wl in wiki_links:
                kb_ref = parse_wiki_kb_ref(wl)
                if kb_ref and not source_kb:
                    source_kb = kb_ref
                daily_ref = parse_wiki_daily_ref(wl)
                if daily_ref and not source_daily:
                    source_daily = daily_ref

            innovations.append(Innovation(
                id=inno_id,
                innovation_type=fields.get("创新点类型", ""),
                description=fields.get("创新点", ""),
                source_paper=fields.get("来源论文", ""),
                source_daily_report=source_daily,
                source_kb=source_kb,
                direction=fields.get("可迁移方向", ""),
                suitable_for=fields.get("适合做成", ""),
                credibility=fields.get("可信度", ""),
                status=fields.get("状态", "候选"),
            ))

        return innovations

    def extract_relations(self, innovations: List[Innovation]) -> List[Relation]:
        """从创新点生成关系"""
        relations = []

        for inno in innovations:
            # Innovation → Paper (KB entry)
            if inno.source_kb:
                relations.append(Relation(
                    source_id=inno.id,
                    target_id=inno.source_kb,
                    relation_type="SOURCED_FROM",
                    confidence=0.95,
                    source_file="可能的创新点.md",
                    metadata={"extracted_from_wikilink": True},
                ))

            # Innovation → DailyReport
            if inno.source_daily_report:
                relations.append(Relation(
                    source_id=inno.id,
                    target_id=inno.source_daily_report,
                    relation_type="REPORTED_IN",
                    confidence=0.95,
                    source_file="可能的创新点.md",
                    metadata={"extracted_from_wikilink": True},
                ))

        return relations
