"""
桌面 1.txt → 个人原则 / 历史笔记 实体提取器
==========================================
解析个人生活原则、财务规则、历史笔记为 Guardrail 实体。
"""

import os
import re
from typing import List

from .base import BaseExtractor
from ..kg_config import KG_HASH_CACHE
from ..kg_schema import Guardrail


class DesktopNotesExtractor(BaseExtractor):
    """桌面笔记提取器"""

    def __init__(self, filepath: str):
        super().__init__(filepath, KG_HASH_CACHE)
        self.filepath = filepath

    def extract(self) -> List[Guardrail]:
        if not os.path.exists(self.source_path):
            return []

        with open(self.source_path, "r", encoding="utf-8") as f:
            content = f.read()

        entities = []
        lines = content.strip().split("\n")
        current_section = "个人原则"

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测 section header
            if line in ("历史", "整合"):
                current_section = line
                continue

            # 编号条目：1.xxx 或 1. xxx 或 1、xxx
            match = re.match(r"^(\d+)\.?\s*(.+)$", line)
            if match:
                num = match.group(1)
                text = match.group(2).strip()
                rule_id = f"personal_rule_{num.zfill(3)}"
                domain = f"桌面笔记/{current_section}"

                entities.append(Guardrail(
                    id=rule_id,
                    rule=text[:120],
                    domain=domain,
                    severity="soft",
                    condition=f"编号 {num} — {current_section}",
                    source="Desktop/1.txt",
                ))
            else:
                # 无编号行：历史笔记片段
                rule_id = f"personal_note_{self._slug(line)[:30]}"
                entities.append(Guardrail(
                    id=rule_id,
                    rule=line[:120],
                    domain=f"桌面笔记/{current_section}",
                    severity="soft",
                    condition=current_section,
                    source="Desktop/1.txt",
                ))

        return entities

    @staticmethod
    def _slug(text: str) -> str:
        return re.sub(r"[^\w一-鿿]", "_", text)[:40]
