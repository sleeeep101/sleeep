"""
增量更新器
=========
基于文件 SHA256 hash 对比，检测源文件变更。
"""

import json
import os
from typing import Dict, Set

from ..kg_config import (
    LONG_TERM_KB, TERMINOLOGY_DB, TECHNIQUE_DB, INNOVATION_DB,
    DAILY_REPORTS_DIR, KG_HASH_CACHE,
)
from ..extractors.base import BaseExtractor


class IncrementalUpdater:
    """增量更新器 — 追踪源文件 hash 变化"""

    # 需要监控的源文件/目录
    SOURCE_FILES = [
        LONG_TERM_KB,
        TERMINOLOGY_DB,
        TECHNIQUE_DB,
        INNOVATION_DB,
        DAILY_REPORTS_DIR,
    ]

    def __init__(self, cache_path: str = KG_HASH_CACHE):
        self.cache_path = cache_path
        self._cache: Dict[str, str] = {}
        self.load_cache()

    def load_cache(self) -> Dict[str, str]:
        if os.path.exists(self.cache_path):
            with open(self.cache_path, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
        return self._cache

    def save_cache(self) -> None:
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, ensure_ascii=False, indent=2)

    def compute_current_hashes(self) -> Dict[str, str]:
        """计算所有源文件的当前 hash"""
        hashes = {}
        for path in self.SOURCE_FILES:
            if os.path.exists(path):
                extractor = BaseExtractor(path, "")
                hashes[path] = extractor.compute_file_hash()
        return hashes

    def needs_rebuild(self) -> bool:
        """检查是否需要重建"""
        current = self.compute_current_hashes()
        for path in self.SOURCE_FILES:
            if path in current:
                old_hash = self._cache.get(path, "")
                if current[path] != old_hash:
                    return True
        return False

    def changed_files(self) -> Set[str]:
        """返回变更的文件列表"""
        current = self.compute_current_hashes()
        changed = set()
        for path in self.SOURCE_FILES:
            if path in current:
                if current[path] != self._cache.get(path, ""):
                    changed.add(path)
        return changed

    def save_state(self) -> None:
        """保存当前 hash 状态"""
        self._cache = self.compute_current_hashes()
        self.save_cache()
