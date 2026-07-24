"""
academic-workflow 全目录提取器
=============================
覆盖 00_项目总览/03_写作/04_项目/05_选题/07_方法库/prompts/references 等。
"""

import os
import re
from typing import List, Optional

from .base import BaseExtractor
from ..kg_config import KG_HASH_CACHE
from ..kg_schema import Guardrail, Technique, ResearchDirection


class AcademicWorkflowExtractor(BaseExtractor):
    """academic-workflow 全目录实体提取器"""

    def __init__(self, acad_root: str):
        super().__init__(acad_root, KG_HASH_CACHE)
        self.root = acad_root

    def extract(self) -> List:
        entities = []
        entities.extend(self._extract_writing_prompts())
        entities.extend(self._extract_project_files())
        entities.extend(self._extract_group_meeting())
        entities.extend(self._extract_graduation_reqs())
        entities.extend(self._extract_method_library())
        entities.extend(self._extract_core_prompts())
        entities.extend(self._extract_references())
        entities.extend(self._extract_navigation_docs())
        return entities

    def _read(self, path: str, max_chars: int = 5000) -> Optional[str]:
        full = os.path.join(self.root, path)
        if os.path.exists(full):
            try:
                with open(full, "r", encoding="utf-8") as f:
                    return f.read(max_chars)
            except Exception:
                return None
        return None

    def _slug(self, text: str) -> str:
        return re.sub(r"[^\w一-鿿]", "_", text)[:40]

    # ── 03_写_论文写作 ──────────────────────────────

    def _extract_writing_prompts(self) -> List:
        """提取写作 prompts 为 Guardrail 实体"""
        prompt_dir = os.path.join(self.root, "03_写_论文写作", "prompts")
        if not os.path.isdir(prompt_dir):
            return []

        rules = []
        for fname in sorted(os.listdir(prompt_dir)):
            if not fname.endswith(".md"):
                continue
            content = self._read(f"03_写_论文写作/prompts/{fname}", 3000)
            if not content:
                continue
            title = re.search(r"^#\s+(.+)", content, re.MULTILINE)
            name = title.group(1).strip() if title else fname
            first_para = content.split("\n\n")[0][:200] if content else ""

            rules.append(Guardrail(
                id=f"aw_writep_{self._slug(fname)}",
                rule=name,
                domain="academic-workflow/写作Prompt",
                severity="soft",
                condition=first_para,
                source=f"03_写_论文写作/prompts/{fname}",
            ))
        return rules

    # ── 04_SCI三区论文项目 ───────────────────────────

    def _extract_project_files(self) -> List:
        """提取 SCI 论文项目文件"""
        proj_dir = os.path.join(self.root, "04_SCI三区论文项目")
        if not os.path.isdir(proj_dir):
            return []

        items: List[ResearchDirection] = []
        for root, dirs, files in os.walk(proj_dir):
            # 跳过深层嵌套
            depth = root.replace(proj_dir, "").count(os.sep)
            if depth > 3:
                continue
            for fname in files:
                if not fname.endswith(".md") and not fname.endswith(".py"):
                    continue
                rel = os.path.relpath(os.path.join(root, fname), self.root)
                content = self._read(rel, 2000)
                if not content:
                    continue
                title = re.search(r"^#\s+(.+)", content, re.MULTILINE)
                name = title.group(1).strip() if title else fname
                items.append(ResearchDirection(
                    id=f"aw_proj_{self._slug(rel)}",
                    name=f"[SCI项目] {name}",
                    source=rel,
                ))
        return items

    # ── 04_组会PPT ──────────────────────────────────

    def _extract_group_meeting(self) -> List:
        """提取组会 PPT 模板和规则"""
        meeting_dir = os.path.join(self.root, "04_组会PPT")
        if not os.path.isdir(meeting_dir):
            return []

        entities = []
        for sub in ["prompts", "rules", "checklists", "03_PPT模板"]:
            sub_dir = os.path.join(meeting_dir, sub)
            if not os.path.isdir(sub_dir):
                continue
            for fname in sorted(os.listdir(sub_dir)):
                if not fname.endswith(".md"):
                    continue
                rel = f"04_组会PPT/{sub}/{fname}"
                content = self._read(rel, 3000)
                if not content:
                    continue
                title = re.search(r"^#\s+(.+)", content, re.MULTILINE)
                name = title.group(1).strip() if title else fname
                entities.append(Guardrail(
                    id=f"aw_meeting_{self._slug(fname)}",
                    rule=name,
                    domain="academic-workflow/组会PPT",
                    severity="soft",
                    condition=content[:200],
                    source=rel,
                ))
        return entities

    # ── 05_选题与问题库 ──────────────────────────────

    def _extract_graduation_reqs(self) -> List:
        """提取毕业要求"""
        content = self._read("05_选题与问题库/毕业要求_学位论文与发表论文.md")
        if not content:
            return []
        return [Guardrail(
            id="aw_grad_reqs",
            rule="硕士毕业要求",
            domain="academic-workflow/毕业要求",
            severity="hard",
            condition=content[:500],
            source="05_选题与问题库/毕业要求_学位论文与发表论文.md",
        )]

    # ── 07_方法与代码库 ──────────────────────────────

    def _extract_method_library(self) -> List:
        """提取方法库索引"""
        content = self._read("07_方法与代码库/方法库索引.md")
        if not content:
            return []
        sections = re.findall(r"^##\s+(.+)", content, re.MULTILINE)
        return [ResearchDirection(
            id=f"aw_methodlib_{self._slug(s)[:30]}",
            name=s,
            source="07_方法与代码库/方法库索引.md",
        ) for s in sections[:20]]

    # ── prompts/ ────────────────────────────────────

    def _extract_core_prompts(self) -> List:
        """提取核心 prompt 文件"""
        prompt_dir = os.path.join(self.root, "prompts")
        if not os.path.isdir(prompt_dir):
            return []

        rules = []
        for fname in sorted(os.listdir(prompt_dir)):
            if not fname.endswith(".md"):
                continue
            content = self._read(f"prompts/{fname}", 3000)
            if not content:
                continue
            title = re.search(r"^#\s+(.+)", content, re.MULTILINE)
            name = title.group(1).strip() if title else fname
            rules.append(Guardrail(
                id=f"aw_prompt_{self._slug(fname)}",
                rule=name,
                domain="academic-workflow/核心Prompt",
                severity="soft",
                condition=content[:200],
                source=f"prompts/{fname}",
            ))
        return rules

    # ── references/ ─────────────────────────────────

    def _extract_references(self) -> List:
        """提取参考文件"""
        ref_dir = os.path.join(self.root, "references")
        if not os.path.isdir(ref_dir):
            return []

        entities = []
        for root, dirs, files in os.walk(ref_dir):
            depth = root.replace(ref_dir, "").count(os.sep)
            if depth > 2:
                continue
            for fname in files:
                if not fname.endswith(".md"):
                    continue
                rel = os.path.relpath(os.path.join(root, fname), self.root)
                content = self._read(rel, 3000)
                if not content:
                    continue
                title = re.search(r"^#\s+(.+)", content, re.MULTILINE)
                name = title.group(1).strip() if title else fname
                # 推理框架(Concept)还是规则(Guardrail)
                if "reasoning" in fname.lower() or "lens" in fname.lower():
                    entities.append(Guardrail(
                        id=f"aw_ref_{self._slug(fname)}",
                        rule=name,
                        domain="academic-workflow/推理框架",
                        severity="soft",
                        condition=content[:300],
                        source=rel,
                    ))
                else:
                    entities.append(Guardrail(
                        id=f"aw_ref_{self._slug(fname)}",
                        rule=name,
                        domain="academic-workflow/参考",
                        severity="soft",
                        condition=content[:200],
                        source=rel,
                    ))
        return entities

    # ── 00_项目总览与导航 ────────────────────────────

    def _extract_navigation_docs(self) -> List:
        """提取导航参考文档"""
        nav_dir = os.path.join(self.root, "00_项目总览与导航")
        if not os.path.isdir(nav_dir):
            return []

        entities = []
        for sub in ["references/references", ""]:
            sub_dir = os.path.join(nav_dir, sub) if sub else nav_dir
            if not os.path.isdir(sub_dir):
                continue
            for fname in sorted(os.listdir(sub_dir)):
                if not fname.endswith(".md"):
                    continue
                rel = os.path.relpath(os.path.join(sub_dir, fname), self.root)
                content = self._read(rel, 2000)
                if not content:
                    continue
                title = re.search(r"^#\s+(.+)", content, re.MULTILINE)
                name = title.group(1).strip() if title else fname
                entities.append(Guardrail(
                    id=f"aw_nav_{self._slug(fname)}",
                    rule=name,
                    domain="academic-workflow/导航参考",
                    severity="soft",
                    condition=content[:200],
                    source=rel,
                ))
        return entities
