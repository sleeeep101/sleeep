"""
知识图谱 Schema
==============
所有实体和关系的 dataclass 定义。
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class EntityType(str, Enum):
    Paper = "Paper"
    Term = "Term"
    Technique = "Technique"
    Innovation = "Innovation"
    DailyReport = "DailyReport"
    Method = "Method"
    Concept = "Concept"
    Guardrail = "Guardrail"
    Script = "Script"
    ResearchDirection = "ResearchDirection"


# ── 实体 Dataclasses ──────────────────────────────────

@dataclass
class Paper:
    """论文笔记实体 — 从长期知识库.md 解析"""
    id: str                          # KB-2026-07-21-01 或 Paper_ID: 2026-06-07_F01
    title: str                       # 论文标题
    entity_type: str = "Paper"
    authors: str = ""                # 作者字符串
    year: Optional[int] = None       # 发表年份
    source: str = ""                 # 期刊/arXiv
    doi: str = ""                    # DOI
    score: Optional[int] = None      # 评分 /100
    grade: str = ""                  # A/B/C/X
    topics: List[str] = field(default_factory=list)   # 主题标签
    summary: str = ""                # 一句话总结
    methods: List[str] = field(default_factory=list)   # 方法列表
    transferability: str = ""        # 可迁移到GIS的点
    credibility: str = ""            # 可信度
    reading_level: str = ""          # 全文证据状态
    fulltext_path: str = ""          # 全文PDF路径
    note_path: str = ""              # 阅读笔记路径 (note.md)
    block_content: str = ""          # 长期知识库中的完整条目原文（全文背诵用）
    kb_date: str = ""                # 入库日期 (YYYY-MM-DD)
    reason: str = ""                 # 加入理由

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}

    @property
    def label(self) -> str:
        return f"{self.id}: {self.title[:60]}"


@dataclass
class Term:
    """专业术语实体 — 从专业术语库.md 解析"""
    id: str                          # A-001
    english: str = ""                # 英文名
    chinese: str = ""                # 中文名
    entity_type: str = "Term"
    category: str = ""               # 分类字母 A-Z
    category_name: str = ""          # 分类中文名
    explanation: str = ""            # 解释
    sources: List[str] = field(default_factory=list)  # 来源论文
    date_added: str = ""             # 入库日期
    related_terms: List[str] = field(default_factory=list)  # 关联术语ID

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}

    @property
    def label(self) -> str:
        return f"{self.id}: {self.chinese} ({self.english[:40]})"


@dataclass
class Technique:
    """写作技法实体 — 从学术写作技法库.md 解析"""
    id: str                          # 技法-Method-001
    name: str = ""                   # 技法名称
    entity_type: str = "Technique"
    category: str = ""               # 技法分类（Intro/Method/Result等）
    category_name: str = ""          # 分类中文名
    template: str = ""               # 技法模板
    usage: str = ""                  # 怎么用
    scenarios: List[str] = field(default_factory=list)  # 适用场景
    sources: List[str] = field(default_factory=list)    # 来源（作者+年份）
    date_added: str = ""             # 入库日期
    complements: List[str] = field(default_factory=list)  # 互补技法ID

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}

    @property
    def label(self) -> str:
        return f"{self.id}: {self.name[:60]}"


@dataclass
class Innovation:
    """创新点实体 — 从可能的创新点.md 解析"""
    id: str                          # INNO-2026-06-22-01
    entity_type: str = "Innovation"
    innovation_type: str = ""        # 方法迁移/场景迁移/数据融合/自动化流程
    description: str = ""            # 创新点描述
    source_paper: str = ""           # 来源论文标题
    source_daily_report: str = ""    # 来源日报文件名
    source_kb: str = ""              # 对应 KB 条目 ID
    direction: str = ""              # 可迁移方向
    suitable_for: str = ""           # 适合做成
    credibility: str = ""            # 可信度
    status: str = "候选"             # 状态

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}

    @property
    def label(self) -> str:
        return f"{self.id}: {self.description[:60]}"


@dataclass
class DailyReport:
    """日报实体"""
    id: str                          # 2026-07-21_论文阅读日报
    date: str = ""                   # YYYY-MM-DD
    entity_type: str = "DailyReport"
    report_type: str = "paper_reading"  # paper_reading | project_supervision | ETF
    path: str = ""                   # 文件路径
    paper_count: int = 0             # 论文数量
    top_directions: List[str] = field(default_factory=list)  # 主要覆盖方向
    summary: str = ""                # 概览摘要
    content: str = ""                # 全文内容（从md文件读取）

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}

    @property
    def label(self) -> str:
        return f"{self.id} ({self.paper_count}篇)"


@dataclass
class Method:
    """方法实体"""
    id: str                          # method_random_forest
    entity_type: str = "Method"
    canonical_name: str = ""         # 标准名称
    aliases: List[str] = field(default_factory=list)  # 别名
    category: str = ""               # ML / GIS / RemoteSensing / Statistics / Geomorphology

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}

    @property
    def label(self) -> str:
        return self.canonical_name


@dataclass
class Concept:
    """推理概念实体 — 从 reasoning-lens.md 解析"""
    id: str                          # concept_L1
    entity_type: str = "Concept"
    layer: str = ""                  # L1-L8
    name: str = ""                   # 概念名称
    description: str = ""            # 描述
    questions: List[str] = field(default_factory=list)  # 阅读/写作/研究设计问题
    source: str = "reasoning-lens.md"

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}

    @property
    def label(self) -> str:
        return f"{self.layer}: {self.name}"


@dataclass
class Guardrail:
    """规则/护轨实体"""
    id: str                          # guardrail_crs_distance
    entity_type: str = "Guardrail"
    rule: str = ""                   # 规则内容
    domain: str = ""                 # 领域 (GIS/CRS, Statistics, DEM, etc.)
    severity: str = "hard"           # hard / soft
    condition: str = ""              # 触发条件
    source: str = ""                 # 来源文件

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}

    @property
    def label(self) -> str:
        return f"[{self.domain}] {self.rule[:60]}"


@dataclass
class Script:
    """脚本实体"""
    id: str                          # script_daily_paper_curator
    entity_type: str = "Script"
    path: str = ""                   # 相对路径
    purpose: str = ""                # 用途
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    schedule: str = ""               # 运行计划

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}

    @property
    def label(self) -> str:
        return f"{self.id}: {self.purpose[:60]}"


@dataclass
class ResearchDirection:
    """研究方向实体"""
    id: str                          # direction_01
    entity_type: str = "ResearchDirection"
    name: str = ""                   # 方向名称
    keywords: List[str] = field(default_factory=list)
    priority: int = 0                 # 优先级
    source: str = "paper_grading_config.json"

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}

    @property
    def label(self) -> str:
        return self.name


# ── 关系 Dataclass ────────────────────────────────────

@dataclass
class Relation:
    """知识图谱中的关系（边）"""
    source_id: str                   # 源节点 ID
    target_id: str                   # 目标节点 ID
    relation_type: str               # 关系类型
    confidence: float = 1.0          # 置信度 (0-1)
    source_file: str = ""            # 来源文件/规则
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.relation_type,
            "confidence": self.confidence,
            "source_file": self.source_file,
            "metadata": self.metadata,
        }


# ── 实体注册表：类型 → dataclass ──────────────────────
ENTITY_CLASS_MAP = {
    "Paper": Paper,
    "Term": Term,
    "Technique": Technique,
    "Innovation": Innovation,
    "DailyReport": DailyReport,
    "Method": Method,
    "Concept": Concept,
    "Guardrail": Guardrail,
    "Script": Script,
    "ResearchDirection": ResearchDirection,
}
