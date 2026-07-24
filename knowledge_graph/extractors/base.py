"""
提取器基类
=========
提供增量检测（文件 hash）、缓存、公共工具。
"""

import hashlib
import json
import os
import re
from typing import List, Optional, Dict, Any

from ..kg_config import FIELD_PATTERN, WIKI_LINK_PATTERN


class BaseExtractor:
    """提取器基类"""

    def __init__(self, source_path: str, hash_cache_path: str):
        self.source_path = source_path
        self.hash_cache_path = hash_cache_path
        self._hash_cache: Dict[str, str] = {}

    def load_hash_cache(self) -> Dict[str, str]:
        """加载 hash 缓存"""
        if os.path.exists(self.hash_cache_path):
            with open(self.hash_cache_path, "r", encoding="utf-8") as f:
                self._hash_cache = json.load(f)
        return self._hash_cache

    def save_hash_cache(self) -> None:
        """保存 hash 缓存"""
        with open(self.hash_cache_path, "w", encoding="utf-8") as f:
            json.dump(self._hash_cache, f, ensure_ascii=False, indent=2)

    def compute_file_hash(self) -> str:
        """计算文件 SHA256"""
        sha = hashlib.sha256()
        if os.path.isfile(self.source_path):
            with open(self.source_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha.update(chunk)
        elif os.path.isdir(self.source_path):
            # 目录：对所有文件 hash 再综合
            for root, _, files in sorted(os.walk(self.source_path)):
                for fname in sorted(files):
                    fpath = os.path.join(root, fname)
                    sha.update(fpath.encode())
                    sha.update(str(os.path.getmtime(fpath)).encode())
        return sha.hexdigest()

    def has_changed(self) -> bool:
        """检查源文件/目录是否变更"""
        current_hash = self.compute_file_hash()
        cached_hash = self._hash_cache.get(self.source_path, "")
        if current_hash != cached_hash:
            self._hash_cache[self.source_path] = current_hash
            return True
        return False

    def extract(self) -> List[Any]:
        """子类实现：解析源数据 → 实体列表"""
        raise NotImplementedError


# ── 公共解析工具 ──────────────────────────────────────

def parse_fields(text: str) -> Dict[str, str]:
    """从 Markdown 文本块中提取 - **字段:** 值 对"""
    fields = {}
    for line in text.strip().split("\n"):
        m = re.match(FIELD_PATTERN, line.strip())
        if m:
            key = m.group(1).strip().rstrip(":：").strip()
            value = m.group(2).strip()
            fields[key] = value
    return fields


def extract_wiki_links(text: str) -> List[str]:
    """从文本中提取 [[wiki-link]]"""
    return re.findall(WIKI_LINK_PATTERN, text)


def parse_wiki_kb_ref(wiki_link: str) -> Optional[str]:
    """解析 [[长期知识库#KB-2026-07-21-01]] → KB-ID"""
    if "#" in wiki_link:
        ref = wiki_link.split("#")[-1]
        if ref.startswith("KB-") or ref.startswith("Paper_ID"):
            return ref
    return None


def parse_wiki_daily_ref(wiki_link: str) -> Optional[str]:
    """解析 [[2026-07-21_论文阅读日报]] → 日报ID"""
    if "_论文阅读日报" in wiki_link:
        return wiki_link.strip("[]")
    return None


def normalize_method_name(raw: str, method_map: Dict[str, str]) -> Optional[str]:
    """将原始方法名标准化"""
    lower = raw.strip().lower()
    # 直接匹配
    if lower in method_map:
        return method_map[lower]
    # 模糊匹配：raw 是否包含关键词
    for key, canonical in method_map.items():
        if len(key) > 3 and key in lower:
            return canonical
    return None
