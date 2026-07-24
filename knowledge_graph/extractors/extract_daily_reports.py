"""
日报 → DailyReport 实体提取器
============================
扫描 01_每日论文/ 目录，提取每份日报的概览信息。
同时扫描 Personal-Brain/reports/daily/ 提取项目监管报告。
"""

import re
import os
from typing import List, Optional

from .base import BaseExtractor
from ..kg_config import (
    DAILY_REPORTS_DIR, PERSONAL_BRAIN_DAILY,
    DAILY_REPORT_FILENAME_PATTERN, SUPERVISION_REPORT_FILENAME_PATTERN,
    KG_HASH_CACHE,
)
from ..kg_schema import DailyReport


class DailyReportExtractor(BaseExtractor):
    """日报提取器（覆盖论文阅读日报 + 项目监管日报）"""

    def __init__(self):
        super().__init__(DAILY_REPORTS_DIR, KG_HASH_CACHE)

    def extract(self) -> List[DailyReport]:
        reports: List[DailyReport] = []
        seen_ids: set = set()

        # 1. 论文阅读日报
        if os.path.isdir(DAILY_REPORTS_DIR):
            for fname in sorted(os.listdir(DAILY_REPORTS_DIR)):
                match = re.match(DAILY_REPORT_FILENAME_PATTERN, fname)
                if not match:
                    continue
                date_str = match.group(1)
                report_id = f"{date_str}_论文阅读日报"
                if report_id in seen_ids:
                    continue
                seen_ids.add(report_id)

                fpath = os.path.join(DAILY_REPORTS_DIR, fname)
                report = self._parse_paper_reading_report(report_id, date_str, fpath)
                reports.append(report)

        # 2. 项目监管日报
        if os.path.isdir(PERSONAL_BRAIN_DAILY):
            for fname in sorted(os.listdir(PERSONAL_BRAIN_DAILY)):
                match = re.match(SUPERVISION_REPORT_FILENAME_PATTERN, fname)
                if not match:
                    continue
                date_str = match.group(1)
                report_id = f"{date_str}_每日项目监管报告"
                if report_id in seen_ids:
                    continue
                seen_ids.add(report_id)

                fpath = os.path.join(PERSONAL_BRAIN_DAILY, fname)
                report = self._parse_supervision_report(report_id, date_str, fpath)
                reports.append(report)

        return reports

    def _parse_paper_reading_report(self, report_id: str, date_str: str, fpath: str) -> DailyReport:
        """解析论文阅读日报"""
        paper_count = 0
        top_directions: List[str] = []
        summary = ""

        try:
            with open(fpath, "r", encoding="utf-8") as f:
                full_content = f.read(50000)  # 全文读取（上限50K）

            # 提取论文总数
            count_match = re.search(r"检索论文总数\s*[:：|]\s*(\d+)", full_content)
            if not count_match:
                count_match = re.search(r"(\d+)\s*篇", full_content)
            if count_match:
                paper_count = int(count_match.group(1))

            # 提取主要方向
            direction_section = re.search(r"方向匹配度分布(.*?)(?=##|\Z)", full_content, re.DOTALL)
            if direction_section:
                dir_matches = re.findall(r"[（(]([A-C])[）)]\s*[:：]\s*(\S+)", direction_section.group(0))
                top_directions = [d for grade, d in dir_matches if grade in ("A", "B")]

            # 提取概览摘要
            overview_match = re.search(r"概览.*?\n(.*?)(?=\n##)", full_content, re.DOTALL)
            if overview_match:
                summary = overview_match.group(1).strip()[:200]
            else:
                first_para = re.search(r"^#.*?\n\n(.+?)(?=\n##|\n#)", full_content, re.DOTALL)
                if first_para:
                    summary = first_para.group(1).strip()[:200]

        except Exception:
            pass

        return DailyReport(
            id=report_id,
            date=date_str,
            report_type="paper_reading",
            path=fpath,
            paper_count=paper_count,
            top_directions=top_directions,
            summary=summary,
            content=full_content,  # 全文背诵
        )

    def _parse_supervision_report(self, report_id: str, date_str: str, fpath: str) -> DailyReport:
        """解析项目监管日报"""
        summary = ""
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read(3000)

            # 提取总体状态
            status_match = re.search(r"总体状态\s*[:：]\s*(.+?)(?:\n|$)", content)
            if status_match:
                summary = f"总体状态: {status_match.group(1).strip()}"
        except Exception:
            pass

        return DailyReport(
            id=report_id,
            date=date_str,
            report_type="project_supervision",
            path=fpath,
            summary=summary,
        )
