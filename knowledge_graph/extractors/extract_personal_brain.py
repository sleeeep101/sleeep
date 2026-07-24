"""
Personal-Brain → Project / AgentRule / MaintenanceRule 实体提取器
=================================================================
从 Personal-Brain 目录提取项目管理、Agent 配置、维护规则等结构化实体。
"""

import os
import re
from typing import List

from .base import BaseExtractor
from ..kg_config import KG_HASH_CACHE
from ..kg_schema import DailyReport  # 复用日报类型或新建


class PersonalBrainExtractor(BaseExtractor):
    """Personal-Brain 实体提取器"""

    def __init__(self, brain_root: str):
        # brain_root: <LOCAL_PATH>
        super().__init__(brain_root, KG_HASH_CACHE)
        self.brain_root = brain_root

    def extract(self) -> List:
        """提取 Personal-Brain 中的所有结构化实体"""
        entities = []

        # 1. Agent 规则
        entities.extend(self._extract_agent_rules())

        # 2. 项目描述
        entities.extend(self._extract_projects())

        # 3. 维护规则
        entities.extend(self._extract_maintenance_rules())

        # 4. 核心原则
        entities.extend(self._extract_core_principles())

        # 5. 职业规划
        entities.extend(self._extract_career_items())

        return entities

    def _extract_agent_rules(self) -> List:
        """提取 Agent 规则实体"""
        from ..kg_schema import Guardrail  # 复用规则实体类型

        agents_dir = os.path.join(self.brain_root, "agents")
        if not os.path.isdir(agents_dir):
            return []

        rules = []
        for fname in sorted(os.listdir(agents_dir)):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(agents_dir, fname)

            # 文件名即规则 ID
            rule_id = f"pb_rule_{os.path.splitext(fname)[0]}"
            rule_name = os.path.splitext(fname)[0]

            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read(2000)
                # 取第一段作为规则简述
                first_para = content.strip().split("\n\n")[0] if content else ""
                rule_text = first_para[:200]
            except Exception:
                rule_text = ""

            rules.append(Guardrail(
                id=rule_id,
                rule=f"{rule_name}: {rule_text}",
                domain="Personal-Brain/Agent",
                severity="hard",
                source=f"Personal-Brain/agents/{fname}",
            ))

        return rules

    def _extract_projects(self) -> List:
        """提取项目描述实体"""
        from ..kg_schema import ResearchDirection  # 复用

        projects_dir = os.path.join(self.brain_root, "projects")
        if not os.path.isdir(projects_dir):
            return []

        projects = []
        for fname in sorted(os.listdir(projects_dir)):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(projects_dir, fname)
            proj_id = f"pb_project_{os.path.splitext(fname)[0]}"

            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read(3000)

                # 取标题
                title_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
                name = title_match.group(1).strip() if title_match else fname

                # 找关键词
                keywords = []
                kw_section = re.search(r"关键词|标签|技术栈|方向", content)
                if kw_section:
                    kw_line = content[kw_section.end():].strip().split("\n")[0]
                    keywords = [k.strip() for k in re.split(r"[;；,，、]", kw_line) if k.strip()]

                projects.append(ResearchDirection(
                    id=proj_id,
                    name=name,
                    keywords=keywords,
                    source=f"Personal-Brain/projects/{fname}",
                ))
            except Exception:
                pass

        return projects

    def _extract_maintenance_rules(self) -> List:
        """提取维护规则实体"""
        from ..kg_schema import Guardrail

        maint_dir = os.path.join(self.brain_root, "maintenance")
        if not os.path.isdir(maint_dir):
            return []

        rules = []
        for fname in sorted(os.listdir(maint_dir)):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(maint_dir, fname)
            rule_id = f"pb_maint_{os.path.splitext(fname)[0]}"

            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read(2000)
                title_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
                rule_name = title_match.group(1) if title_match else fname
                first_para = content.strip().split("\n\n")[0] if content else ""
            except Exception:
                rule_name = fname
                first_para = ""

            rules.append(Guardrail(
                id=rule_id,
                rule=rule_name,
                domain="Personal-Brain/Maintenance",
                severity="soft",
                condition=first_para[:200],
                source=f"Personal-Brain/maintenance/{fname}",
            ))

        return rules

    def _extract_core_principles(self) -> List:
        """提取核心原则实体"""
        from ..kg_schema import Guardrail

        principles_file = os.path.join(self.brain_root, "核心原则与固定问法系统_2026-06-03.md")
        if not os.path.exists(principles_file):
            return []

        try:
            with open(principles_file, "r", encoding="utf-8") as f:
                content = f.read(5000)
        except Exception:
            return []

        rules = []
        # 按 ## 拆分，每个 section 是一条原则
        sections = re.split(r"\n##\s+", content)
        for i, section in enumerate(sections[1:], 1):  # 跳过文件头
            lines = section.strip().split("\n")
            title = lines[0].strip() if lines else f"原则{i}"
            body = " ".join(lines[1:3])[:200] if len(lines) > 1 else ""

            rules.append(Guardrail(
                id=f"pb_principle_{i:03d}",
                rule=title,
                domain="Personal-Brain/核心原则",
                severity="hard",
                condition=body,
                source="核心原则与固定问法系统_2026-06-03.md",
            ))

        return rules

    def _extract_career_items(self) -> List:
        """提取职业规划实体"""
        from ..kg_schema import ResearchDirection  # 复用

        career_dir = os.path.join(self.brain_root, "career")
        if not os.path.isdir(career_dir):
            return []

        items = []
        for fname in sorted(os.listdir(career_dir)):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(career_dir, fname)
            item_id = f"pb_career_{os.path.splitext(fname)[0]}"

            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read(2000)
                title_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
                name = title_match.group(1) if title_match else fname
            except Exception:
                name = fname

            items.append(ResearchDirection(
                id=item_id,
                name=name,
                source=f"Personal-Brain/career/{fname}",
            ))

        return items
