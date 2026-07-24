"""
已读论文清单 → ReadingRecord 实体提取器
=====================================
解析 Markdown 表格：阅读日期 | 论文标题 | 作者 | 年份 | 来源 | DOI | 语言 | 获取方式
"""

import os
import re
from typing import List

from .base import BaseExtractor
from ..kg_config import KG_HASH_CACHE
from ..kg_schema import DailyReport


class ReadingListExtractor(BaseExtractor):
    """已读论文清单提取器"""

    def __init__(self, acad_root: str):
        self.reading_list_path = os.path.join(
            acad_root, "01_读_论文阅读与复盘", "02_论文阅读库", "已读论文清单.md"
        )
        super().__init__(self.reading_list_path, KG_HASH_CACHE)

    def extract(self) -> List:
        if not os.path.exists(self.source_path):
            return []

        records = []
        try:
            with open(self.source_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return records

        # 解析表格行
        table_rows = re.findall(
            r"\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\d{4})\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|",
            content
        )

        seen = set()
        for row in table_rows:
            date, title, authors, year, source, doi, lang, method = row
            title = title.strip()
            if not title or title == "论文标题":
                continue

            # 用 title + date 做去重
            key = f"{date}|{title[:80]}"
            if key in seen:
                continue
            seen.add(key)

            record_id = f"read_{date}_{self._slug(title)[:30]}"
            records.append(DailyReport(
                id=record_id,
                date=date,
                report_type="reading_record",
                path=f"已读论文清单.md#{date}",
                summary=f"{title} ({authors}, {year}) [{source}]",
                paper_count=1,
            ))

        return records

    @staticmethod
    def _slug(text: str) -> str:
        return re.sub(r"[^\w一-鿿]", "_", text)[:40]
