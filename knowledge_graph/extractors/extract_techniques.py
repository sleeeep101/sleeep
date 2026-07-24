"""
学术写作技法库.md → Technique 实体提取器
======================================
解析 ### 技法-Category-NNN｜技法名 格式。
"""

import re
import os
from typing import List

from .base import BaseExtractor, parse_fields
from ..kg_config import TECHNIQUE_HEADER_PATTERN, TECHNIQUE_CATEGORY_MAP, TECHNIQUE_DB, KG_HASH_CACHE
from ..kg_schema import Technique


class TechniqueExtractor(BaseExtractor):
    """写作技法提取器"""

    def __init__(self):
        super().__init__(TECHNIQUE_DB, KG_HASH_CACHE)

    def extract(self) -> List[Technique]:
        if not os.path.exists(self.source_path):
            return []

        techniques: List[Technique] = []
        seen_ids: set = set()

        with open(self.source_path, "r", encoding="utf-8") as f:
            content = f.read()

        current_batch_date = ""

        # 按 ### 拆分（同时提取 ## 日期批次）
        blocks = re.split(r"\n(?=###\s+)", content)

        for block in blocks:
            # 日期批次
            date_match = re.search(r"##\s+(\d{4}-\d{2}-\d{2})", block)
            if date_match:
                current_batch_date = date_match.group(1)

            # 匹配技法 header
            tech_match = re.match(TECHNIQUE_HEADER_PATTERN, block.strip())
            if not tech_match:
                continue

            cat_abbr = tech_match.group(1)
            tech_num = tech_match.group(2)
            tech_name = tech_match.group(3).strip()

            tech_id = f"技法-{cat_abbr}-{tech_num}"
            if tech_id in seen_ids:
                continue
            seen_ids.add(tech_id)

            fields = parse_fields(block)

            # 技法模板
            template = fields.get("技法", "")

            # 怎么用
            usage = fields.get("怎么用", "")

            # 适用场景
            scenarios_raw = fields.get("适用场景", "") or fields.get("场景", "")
            scenarios = [s.strip() for s in re.split(r"[;；,，、]", scenarios_raw) if s.strip()]

            # 来源
            sources_raw = fields.get("来源", "") or fields.get("来源论文", "")
            sources = [s.strip() for s in re.split(r"[;；]", sources_raw) if s.strip()]

            # 入库日期
            date_added = fields.get("入库日期", current_batch_date)

            # 互补技法（"区别于Intro-008"、"与Method-003互补"）
            complements = self._find_complements(block)

            # 分类中文名
            category_name = TECHNIQUE_CATEGORY_MAP.get(cat_abbr, cat_abbr)
            if tech_name.startswith("NEW"):
                # NEW.1 等是新批次的编号，保持原分类
                pass

            techniques.append(Technique(
                id=tech_id,
                name=tech_name,
                category=cat_abbr,
                category_name=category_name,
                template=template,
                usage=usage,
                scenarios=scenarios,
                sources=sources,
                date_added=date_added,
                complements=complements,
            ))

        return techniques

    def _find_complements(self, block: str) -> List[str]:
        """发现互补技法引用"""
        refs = []
        for pattern in [r"区别于\s*(技法-[A-Za-z]+-\d{3})",
                        r"与\s*(技法-[A-Za-z]+-\d{3})\s*互补",
                        r"参见\s*(技法-[A-Za-z]+-\d{3})"]:
            found = re.findall(pattern, block)
            refs.extend(found)
        return list(set(refs))
