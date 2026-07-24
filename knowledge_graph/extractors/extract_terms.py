"""
专业术语库.md → Term 实体提取器
===============================
解析两种格式：
1. ### A-001｜中文名（English Name） — 全字段格式
2. 表格格式：| 英文 | 中文 | 语境 |
"""

import re
import os
from typing import List, Optional

from .base import BaseExtractor, parse_fields
from ..kg_config import TERM_HEADER_PATTERN, TERM_CATEGORY_MAP, TERMINOLOGY_DB, KG_HASH_CACHE
from ..kg_schema import Term


class TermExtractor(BaseExtractor):
    """专业术语提取器"""

    def __init__(self):
        super().__init__(TERMINOLOGY_DB, KG_HASH_CACHE)

    def extract(self) -> List[Term]:
        if not os.path.exists(self.source_path):
            return []

        terms: List[Term] = []
        seen_ids: set = set()

        with open(self.source_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 按 ### 标题拆分
        blocks = re.split(r"\n(?=###\s+)", content)

        current_batch_date = ""

        for block in blocks:
            # 检测日期批次 header
            date_match = re.search(r"##\s+(\d{4}-\d{2}-\d{2})", block)
            if date_match:
                current_batch_date = date_match.group(1)

            # 尝试匹配术语 header
            term_match = re.match(TERM_HEADER_PATTERN, block.strip())
            if not term_match:
                # 可能不是术语条目，跳过
                continue

            cat_letter = term_match.group(1)
            term_num = term_match.group(2)
            term_name_raw = term_match.group(3).strip()

            term_id = f"{cat_letter}-{term_num}"
            if term_id in seen_ids:
                continue
            seen_ids.add(term_id)

            # 解析术语名：中文名（English Name, ABBR）
            chinese = ""
            english = ""
            if "（" in term_name_raw:
                chinese = term_name_raw.split("（")[0].strip()
                english = term_name_raw.split("（")[-1].split("）")[0].strip()
            elif "(" in term_name_raw:
                chinese = term_name_raw.split("(")[0].strip()
                english = term_name_raw.split("(")[-1].split(")")[0].strip()
            else:
                chinese = term_name_raw

            # 解析字段
            fields = parse_fields(block)
            explanation = fields.get("解释", "")
            sources_raw = fields.get("来源", "")
            sources = [s.strip() for s in re.split(r"[;；]", sources_raw) if s.strip()]
            date_added = fields.get("入库日期", current_batch_date)

            # 发现关联术语（在解释文本中的引用）
            related = self._find_term_refs(explanation, block)

            category_name = TERM_CATEGORY_MAP.get(cat_letter, "")

            terms.append(Term(
                id=term_id,
                english=english,
                chinese=chinese,
                category=cat_letter,
                category_name=category_name,
                explanation=explanation,
                sources=sources,
                date_added=date_added,
                related_terms=related,
            ))

        # 解析表格格式术语（较新的批次：2026-07-21, 2026-07-22）
        table_terms = self._parse_table_terms(content)
        for tt in table_terms:
            if tt.id not in seen_ids:
                seen_ids.add(tt.id)
                terms.append(tt)

        return terms

    def _parse_table_terms(self, content: str) -> List[Term]:
        """解析表格格式：| 英文 | 中文 | 语境 |"""
        results = []
        # 找到所有表格块
        table_blocks = re.finditer(
            r"\| 英文 \| 中文 \| 语境 \|.*?\n((?:\|.*\n)+)",
            content
        )
        counter = {}
        for tb in table_blocks:
            rows = tb.group(1).strip().split("\n")
            for row in rows:
                cells = [c.strip() for c in row.split("|") if c.strip()]
                if len(cells) >= 3:
                    english = cells[0]
                    chinese = cells[1]
                    context = cells[2]

                    # 生成唯一 ID（基于英文名的 hash）
                    term_slug = re.sub(r"[^a-z0-9]", "_", english.lower())[:30]
                    base_slug = term_slug or f"table_term_{len(results)}"
                    if base_slug not in counter:
                        counter[base_slug] = 0
                    counter[base_slug] += 1
                    term_id = f"TBL-{base_slug}-{counter[base_slug]:03d}"

                    results.append(Term(
                        id=term_id,
                        english=english,
                        chinese=chinese,
                        explanation=context,
                        category="Z",
                        category_name="交叉/其他 (表格提取)",
                    ))

        return results

    def _find_term_refs(self, explanation: str, block: str) -> List[str]:
        """在解释文本中发现对其他术语的引用"""
        refs = []
        # 匹配 "区别于A-039"、"参见A-009" 等模式
        for pattern in [r"区别于\s*([A-Z]-\d{3})", r"参见\s*([A-Z]-\d{3})",
                        r"([A-Z]-\d{3})"]:
            found = re.findall(pattern, explanation)
            refs.extend(found)
        return list(set(refs))
