"""
桌面 人脉.txt → Contact 实体提取器
=================================
格式：名字 - 认识渠道 | 印象备注 | #标签
每行一个人，空行分隔。
"""

import os, re
from typing import List

from .base import BaseExtractor
from ..kg_config import KG_HASH_CACHE
from ..kg_schema import Guardrail


class ContactsExtractor(BaseExtractor):
    """人脉联系人提取器"""

    def __init__(self, filepath: str):
        super().__init__(filepath, KG_HASH_CACHE)
        self.filepath = filepath

    def extract(self) -> List[Guardrail]:
        if not os.path.exists(self.source_path):
            return []

        with open(self.source_path, "r", encoding="utf-8") as f:
            content = f.read()

        contacts = []
        for line in content.strip().split("\n"):
            line = line.strip()
            # 跳过空行、注释、格式说明
            if not line or line.startswith("#") or line.startswith("加好友") or line.startswith("格式"):
                continue

            # 解析：名字 - 渠道 | 印象 | #标签
            parts = line.split(" - ", 1)
            name = parts[0].strip()
            rest = parts[1].strip() if len(parts) > 1 else ""

            # 提取标签
            tags = re.findall(r"#(\S+)", rest)
            # 分割渠道和印象
            segments = [s.strip() for s in rest.split("|")]
            channel = segments[0] if segments else ""
            impression = segments[1] if len(segments) > 1 else ""
            # 去掉标签部分
            impression_clean = re.sub(r"#\S+", "", impression).strip()

            contact_id = "contact_%s" % re.sub(r"[^\w一-鿿]", "_", name)[:30]

            contacts.append(Guardrail(
                id=contact_id,
                rule="%s | %s | %s" % (name, channel, impression_clean),
                domain="人脉",
                severity="soft",
                condition="认识渠道: %s | 印象: %s | 标签: %s" % (
                    channel, impression_clean, ", ".join(tags)),
                source="Desktop/人脉.txt",
            ))

        return contacts
