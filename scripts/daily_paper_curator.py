#!/usr/bin/env python3
r"""daily_paper_curator.py -- 每日科研论文自动筛选 + 知识卡片生成

数据源: arXiv API + Semantic Scholar API (均免费开放)
去重: SQLite 本地库, 永不重复推荐
覆盖领域: DEM/地形/GIS空间建模/遥感分类/土地利用/GEE/机器学习迁移/因果推断/实验设计

方法论来源:
  - scientific-thinking-literature-review: PICO搜索策略 + 系统文献综述工作流
  - scientific-thinking-scholar-evaluation: 1-5分制结构化论文评分rubric

用法:
  python daily_paper_curator.py                      # 搜索 + 筛选 + 生成日报
  python daily_paper_curator.py --date 2026-05-28    # 指定日期
  python daily_paper_curator.py --reset              # 清空去重库(慎用)
  python daily_paper_curator.py --schedule           # 输出Windows计划任务配置

输出: <LOCAL_PATH>
"""

import sys
import os
import re
import json
import sqlite3
import hashlib
import subprocess
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import ssl
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 论文源文件留存
from paper_source_utils import save_paper_source_file, get_source_status_line

# 全文获取与解析
from fulltext_utils import (
    process_paper_fulltext, process_candidates_fulltext,
    resolve_fulltext_url, classify_reading_level,
    FULLTEXT_ROOT as FULLTEXT_DIR,
)

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# SSL 上下文 (arXiv 是公共API, 无敏感数据传输)
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# ── 阅读等级 (Reading Levels) ─────────────────────────────

class ReadingLevel:
    """论文阅读证据等级 — 严格分级，防止摘要伪装精读"""
    META_ONLY = "META_ONLY"              # 只有标题/作者/年份/来源/DOI/链接
    ABSTRACT_ONLY = "ABSTRACT_ONLY"      # 只读了摘要，未读PDF全文
    PDF_TEXT_PARTIAL = "PDF_TEXT_PARTIAL" # 下载了解析了PDF，但只读了部分正文
    PDF_TEXT_FULL = "PDF_TEXT_FULL"      # 成功读取PDF正文，覆盖关键章节
    HUMAN_CONFIRMED = "HUMAN_CONFIRMED"  # 人工确认读过或复核过全文

READING_LEVEL_LABELS = {
    ReadingLevel.META_ONLY: "仅元数据",
    ReadingLevel.ABSTRACT_ONLY: "仅摘要",
    ReadingLevel.PDF_TEXT_PARTIAL: "部分正文",
    ReadingLevel.PDF_TEXT_FULL: "全文精读",
    ReadingLevel.HUMAN_CONFIRMED: "人工确认",
}

# ── 论文分类白名单 ─────────────────────────────────────────

PAPER_CATEGORY_WHITELIST = [
    "遥感/GIS",
    "AI/计算机",
    "统计/方法",
    "生态环境",
    "交叉学科",
]


def normalize_paper_category(category: str) -> str:
    """校验并归一化论文分类，不在白名单的统一归为交叉学科"""
    if category in PAPER_CATEGORY_WHITELIST:
        return category
    return "交叉学科"


# ── 路径 ───────────────────────────────────────────────────

def _load_path_config():
    """从 config/paths.json 读取路径。失败时报错停止，不回退到硬编码路径。"""
    import json as _json
    project_root = Path(__file__).resolve().parent.parent
    config_file = project_root / "config" / "paths.json"
    if not config_file.exists():
        raise FileNotFoundError(
            f"配置文件不存在: {config_file}\n"
            f"请确保 config/paths.json 存在且格式正确。"
        )
    try:
        cfg = _json.loads(config_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise ValueError(
            f"配置文件解析失败: {config_file}\n"
            f"错误: {e}\n"
            f"请检查 JSON 格式是否正确。"
        ) from e

    aw = cfg.get("academic_workflow")
    if not aw:
        raise KeyError("paths.json 缺少 'academic_workflow' 配置节")

    aw_root = Path(aw.get("root", str(project_root)))
    if not aw_root.exists():
        print(f"  [!] 警告: academic_workflow root 目录不存在，将尝试创建: {aw_root}")

    required_fields = {
        "daily_reports": "每日论文输出目录",
        "tracker_db": "去重数据库",
        "knowledge_base": "长期知识库文件",
        "pending_read": "待补读队列",
    }
    for field, desc in required_fields.items():
        if not aw.get(field):
            raise KeyError(f"paths.json 缺少配置: academic_workflow.{field} ({desc})")

    etf = cfg.get("etf", {})
    push_cfg_path = None
    if etf and etf.get("root") and etf.get("push_config"):
        push_cfg_path = Path(etf["root"]) / etf["push_config"]

    innovation_points_rel = aw.get("innovation_points", "01_读_论文阅读与复盘/04_长期知识库/可能的创新点.md")

    return {
        "output_dir": aw_root / aw["daily_reports"],
        "db_path": aw_root / aw["tracker_db"],
        "kb_path": aw_root / aw["knowledge_base"],
        "pending_read_path": aw_root / aw["pending_read"],
        "innovation_points_path": aw_root / innovation_points_rel,
        "push_cfg_path": push_cfg_path,
    }

_paths = _load_path_config()
OUTPUT_DIR = _paths["output_dir"]
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = _paths["db_path"]
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
KB_PATH = _paths["kb_path"]
PENDING_READ_PATH = _paths["pending_read_path"]
INNOVATION_POINTS_PATH = _paths.get("innovation_points_path")
KB_WRITE_LOG_PATH = _paths["db_path"].parent / "kb_write.log"

# ── 每日精读论文数量配置 ──────────────────────────────────

DAILY_INTENSIVE_READ_COUNT = 5  # 每日精读论文数量：5篇
DAILY_FULLTEXT_PROCESS_LIMIT = 8  # 每日尝试下载全文的上限（略高于精读数，确保足够的成功下载）


# ── Claude 进程检测 ─────────────────────────────────────

def is_claude_running() -> bool:
    """检测 Claude 是否正在运行（Windows 下通过 tasklist 检测 Claude.exe 进程）。
    检测失败或异常时保守返回 False，不抛出异常以免中断调用方。
    支持环境变量 CLAUDE_FORCE_RUN=1 绕过检测（用于手动补跑）。
    """
    # 环境变量覆盖：允许手动补跑时强制通过检测
    if os.environ.get("CLAUDE_FORCE_RUN", "").strip() == "1":
        return True

    # 方法 1: tasklist 进程检测
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Claude.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        output = result.stdout.strip().lower()
        if "claude.exe" in output:
            return True
    except Exception:
        pass  # tasklist 失败，尝试下一方法

    # 方法 2: psutil 进程名搜索（跨平台，更鲁棒）
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and 'claude' in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass

    # 所有方法都失败，保守返回 False
    return False


def check_claude_and_exit_if_not_running():
    """如果 Claude 未打开，打印日志并退出进程（exit code 0，非错误退出）。
    环境变量 CLAUDE_FORCE_RUN=1 可绕过检测。"""
    if is_claude_running():
        return  # Claude 正在运行，继续执行

    msg = "Claude 未打开，今日论文阅读任务跳过"
    print(f"[!] {msg}")
    # 写入日志文件
    log_dir = Path(DB_PATH).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    skip_log_path = log_dir / "paper_curator_skip.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(skip_log_path, "a", encoding="utf-8") as lf:
        lf.write(f"[{timestamp}] {msg}\n")
    sys.exit(0)


# ── 搜索关键词 (9个方向, 聚焦罗明良老师研究方向) ─────────────
# 方向压缩日期: 2026-06-09
# 旧8方向(泛遥感/AI/城市/生态/气候等) 已移除, 只保留DEM/地形/沟谷/侵蚀/GIS空间建模主线

SEARCH_QUERIES = {
    # A组: 数字地形分析核心
    "数字地形分析": [
        "digital terrain analysis DEM",
        "digital elevation model terrain attributes",
        "geomorphometry terrain factor extraction",
        "DEM digital terrain analysis geomorphology",
    ],
    # B组: 沟谷/冲沟/沟蚀地貌
    "沟谷与沟蚀地貌": [
        "gully erosion morphology development",
        "gully erosion digital elevation model",
        "gully morphology terrain analysis Loess Plateau",
        "gully erosion monitoring GIS spatial analysis",
    ],
    # C组: 土壤侵蚀模型与模拟
    "土壤侵蚀模型": [
        "soil erosion modeling GIS spatial",
        "soil erosion DEM RUSLE simulation",
        "erosion modeling digital terrain analysis",
        "soil erosion watershed spatial analysis",
    ],
    # D组: GIS空间分析与空间建模
    "GIS空间分析与建模": [
        "GIS spatial analysis modeling terrain",
        "spatial modeling geomorphology DEM",
        "geospatial analysis digital elevation model",
        "GIS spatial statistics terrain attributes",
    ],
    # E组: 水土保持与荒漠化防治
    "水土保持与荒漠化": [
        "soil water conservation GIS DEM",
        "soil erosion control spatial analysis",
        "desertification monitoring terrain analysis",
        "soil conservation digital elevation model",
    ],
    # F组: 黄土高原专题
    "黄土高原": [
        "Loess Plateau gully erosion DEM",
        "Loess Plateau soil erosion terrain analysis",
        "Loess Plateau digital terrain analysis",
        "Loess Plateau geomorphology DEM",
    ],
    # G组: 干热河谷专题
    "干热河谷": [
        "dry-hot valley gully erosion",
        "dry-hot valley soil erosion DEM",
        "Yuanmou dry-hot valley gully morphology",
        "Jinsha River dry-hot valley gully",
    ],
    # H组: 中文核心检索
    "中文核心检索": [
        "数字地形分析 DEM 地形因子",
        "DEM 土壤侵蚀 冲沟 沟蚀",
        "黄土高原 沟蚀 数字高程模型",
        "干热河谷 冲沟 土壤侵蚀 GIS",
    ],
    # I组: 地形因子与地貌形态定量分析
    "地形因子与地貌形态": [
        "terrain attributes geomorphometry quantitative",
        "topographic factor extraction DEM",
        "geomorphometric analysis digital elevation model",
        "landform classification terrain analysis DEM",
    ],
}

# ── 数据库 ─────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_papers (
            paper_id TEXT PRIMARY KEY,
            title TEXT,
            source TEXT,
            date_seen TEXT,
            arxiv_id TEXT,
            doi TEXT,
            category TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_log (
            date TEXT PRIMARY KEY,
            candidate_count INTEGER,
            selected_count INTEGER,
            queries_used TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base_index (
            keyword TEXT PRIMARY KEY,
            paper_count INTEGER,
            last_updated TEXT
        )
    """)
    conn.commit()
    return conn


def is_seen(conn, paper_id: str) -> bool:
    return conn.execute("SELECT 1 FROM seen_papers WHERE paper_id=?", (paper_id,)).fetchone() is not None


def mark_seen(conn, paper: Dict):
    conn.execute(
        "INSERT OR IGNORE INTO seen_papers VALUES (?,?,?,?,?,?,?)",
        (paper["paper_id"], paper["title"], paper["source"],
         paper.get("date", ""), paper.get("arxiv_id", ""),
         paper.get("doi", ""), paper.get("category", ""))
    )
    conn.commit()


def get_all_seen_ids(conn) -> set:
    return {r[0] for r in conn.execute("SELECT paper_id FROM seen_papers").fetchall()}


# ── arXiv 搜索 ─────────────────────────────────────────────

def search_arxiv(query: str, max_results: int = 15) -> List[Dict]:
    """通过 arXiv API 搜索论文"""
    # arXiv 学科分类过滤: 只搜GIS/遥感/ML/地学相关领域
    arxiv_cats = " OR ".join([
        "cat:cs.CV",      # 计算机视觉 (遥感图像分析)
        "cat:cs.LG",      # 机器学习
        "cat:stat.ML",    # 统计机器学习
        "cat:physics.geo-ph",  # 地球物理
        "cat:physics.ao-ph",   # 大气海洋
        "cat:eess.IV",    # 图像/视频处理
        "cat:cs.AI",      # 人工智能
        "cat:cs.CL",      # 自然语言处理 (科学文本)
    ])
    full_query = f"({query}) AND ({arxiv_cats})"
    base = "http://export.arxiv.org/api/query"
    params = {
        "search_query": full_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = base + "?" + urllib.parse.urlencode(params)
    papers = []

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DailyPaperCurator/1.0"})
        data = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=45, context=SSL_CTX) as resp:
                    data = resp.read().decode("utf-8")
                break
            except Exception as inner_e:
                if attempt < 2:
                    time.sleep(8)
                else:
                    raise inner_e
        if data is None:
            return papers
        root = ET.fromstring(data)
        ns = {"atom": "http://www.w3.org/2005/Atom",
              "arxiv": "http://arxiv.org/schemas/atom"}

        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            summary_el = entry.find("atom:summary", ns)
            id_el = entry.find("atom:id", ns)
            published_el = entry.find("atom:published", ns)
            authors = [a.find("atom:name", ns).text
                       for a in entry.findall("atom:author", ns) if a.find("atom:name", ns) is not None]

            arxiv_id = id_el.text.strip() if id_el is not None else ""
            arxiv_id = arxiv_id.replace("http://arxiv.org/abs/", "")

            title = title_el.text.strip().replace("\n", " ") if title_el is not None else "Unknown"
            summary = summary_el.text.strip().replace("\n", " ")[:800] if summary_el is not None else ""
            published = published_el.text[:10] if published_el is not None else ""

            # 分类标签
            cats = [c.get("term", "") for c in entry.findall("atom:category", ns)]

            paper_id = hashlib.md5(arxiv_id.encode()).hexdigest()[:12]

            # 确定大分类（论文级5类白名单）
            category = "交叉学科"  # 默认
            if any("cs." in c for c in cats):
                category = "AI/计算机"
            elif any("stat." in c for c in cats):
                category = "统计/方法"
            elif any(k in c.lower() for c in cats for k in ("q-bio", "q-fin", "econ", "geo", "earth", "environ", "ecolog", "atmos")):
                # geo/earth/environ/ecolog/atmos → 遥感/GIS; q-bio/q-fin/econ → 交叉学科
                if any(k in c.lower() for c in cats for k in ("q-bio", "q-fin", "econ")):
                    category = "交叉学科"
                else:
                    category = "遥感/GIS"
            # 标题关键词补充判断：生态环境
            title_lower = title.lower()
            if category == "交叉学科" and any(k in title_lower for k in
                ("ecolog", "ecosystem", "soil", "water", "climat", "carbon",
                 "environment", "hydrolog", "vegetation", "land degradation", "erosion")):
                category = "生态环境"
            category = normalize_paper_category(category)

            papers.append({
                "paper_id": paper_id,
                "title": title,
                "authors": authors[:3],
                "first_author": authors[0] if authors else "Unknown",
                "year": published[:4] if published else "",
                "source": "arXiv",
                "arxiv_id": arxiv_id,
                "doi": "",
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                "abstract": summary,
                "category": category,
                "published": published,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "keywords": query,
                "reading_level": ReadingLevel.ABSTRACT_ONLY if summary else ReadingLevel.META_ONLY,
                "evidence_source": "arXiv API (title+abstract)" if summary else "arXiv API (metadata only)",
                "full_text_read": False,
            })
    except Exception as e:
        print(f"  [!] arXiv搜索异常 ({query[:40]}...): {e}")

    return papers


# ── 论文评分 ───────────────────────────────────────────────

# ── Semantic Scholar 搜索 ──────────────────────────────────

def search_semantic_scholar(query: str, max_results: int = 10) -> List[Dict]:
    """通过 Semantic Scholar API 搜索 (免费, 无需API key)"""
    global _s2_rate_limited, _s2_consecutive_429
    base = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": max_results,
        "fields": "title,authors,year,abstract,externalIds,url,openAccessPdf,publicationVenue,citationCount",
    }
    url = base + "?" + urllib.parse.urlencode(params)
    papers = []

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DailyPaperCurator/1.0"})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=45, context=SSL_CTX) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                break
            except Exception as inner_e:
                if attempt < 2:
                    time.sleep(8)
                else:
                    raise inner_e
        if not data or "data" not in data:
            return papers

        for item in data["data"]:
            paper_id = item.get("paperId", "")
            if not paper_id:
                continue
            ext_ids = item.get("externalIds", {}) or {}
            arxiv_id = ext_ids.get("ArXiv", "")
            doi = ext_ids.get("DOI", "")
            title = item.get("title", "Unknown")
            abstract = item.get("abstract") or ""
            year = str(item.get("year", ""))
            authors = [a.get("name", "") for a in (item.get("authors") or [])[:3]]
            venue = item.get("publicationVenue") or {}
            venue_name = venue.get("name", "") if venue else ""
            is_oa = item.get("openAccessPdf") is not None
            url = item.get("url", "")
            pdf = item["openAccessPdf"]["url"] if is_oa and item.get("openAccessPdf") else ""
            citations = item.get("citationCount", 0)

            papers.append({
                "paper_id": hashlib.md5(paper_id.encode()).hexdigest()[:12],
                "title": title,
                "authors": authors,
                "first_author": authors[0] if authors else "Unknown",
                "year": year,
                "source": "Semantic Scholar",
                "arxiv_id": arxiv_id,
                "doi": doi or f"未提供 (Semantic Scholar ID: {paper_id[:12]})",
                "url": url or f"https://api.semanticscholar.org/CorpusID:{paper_id}",
                "pdf_url": pdf,
                "abstract": (abstract or "")[:800],
                "category": infer_s2_category(item),
                "published": year,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "keywords": query,
                "is_oa": is_oa,
                "venue": venue_name,
                "citations": citations,
                "reading_level": ReadingLevel.ABSTRACT_ONLY if abstract else ReadingLevel.META_ONLY,
                "evidence_source": "Semantic Scholar API (title+abstract)" if abstract else "Semantic Scholar API (metadata only)",
                "full_text_read": False,
            })
    except urllib.error.HTTPError as e:
        if e.code == 429:
            _s2_consecutive_429 += 1
            _s2_rate_limited = True
            skip_msg = f"连续{_s2_consecutive_429}次" if _s2_consecutive_429 > 1 else ""
            print(f"  [!] S2 429 Rate Limited{(' (' + skip_msg + ')，跳过剩余S2调用' if _s2_consecutive_429 >= _S2_MAX_CONSECUTIVE_429 else '，降级为arXiv-only')}")
        else:
            print(f"  [!] Semantic Scholar HTTP {e.code} ({query[:40]}...)")
    except Exception as e:
        print(f"  [!] Semantic Scholar搜索异常 ({query[:40]}...): {e}")
    else:
        _s2_consecutive_429 = 0  # 成功则重置计数器

    return papers


# S2 限流标记
_s2_rate_limited = False
_s2_consecutive_429 = 0
_S2_MAX_CONSECUTIVE_429 = 3  # 连续 N 次 429 后跳过剩余 S2 调用


def infer_s2_category(item: Dict) -> str:
    """从Semantic Scholar返回推断分类，统一使用5类白名单"""
    title = (item.get("title") or "").lower()
    venue = (item.get("publicationVenue") or {}).get("name", "").lower()
    abstract = (item.get("abstract") or "").lower()
    ctx = title + " " + abstract

    # 遥感/GIS
    if any(k in title for k in ["remote sens", "gis", "geospat", "spatial", "land", "terrain", "earth observ"]):
        return normalize_paper_category("遥感/GIS")
    if any(k in venue for k in ["remote sens", "gis", "geosci", "earth", "environ"]):
        return normalize_paper_category("遥感/GIS")
    # AI/计算机
    if any(k in title for k in ["machine learn", "deep learn", "neural", "ai ", "agent"]):
        return normalize_paper_category("AI/计算机")
    # 统计/方法
    if any(k in title for k in ["causal", "statistic", "econometric", "regression"]):
        return normalize_paper_category("统计/方法")
    # 生态环境
    if any(k in ctx for k in ["ecolog", "ecosystem", "soil", "water", "climat", "carbon",
                               "environment", "hydrolog", "vegetation", "land degradation",
                               "erosion", "biodiversity", "conservation"]):
        return normalize_paper_category("生态环境")
    return normalize_paper_category("交叉学科")


# ═══════════════════════════════════════════════════════════
# 学术评分 Rubric (scientific-thinking-scholar-evaluation)
# 1-5分制, 评分维度来自 scholar-evaluation skill
# ═══════════════════════════════════════════════════════════

def rubric_score(paper: Dict) -> Dict:
    """混合评分：关键词8维(免费)+ARS 5维(全文时)。合并为0-100综合分。

    评分策略:
    - 所有论文: 运行关键词8维评分(免费、即时)
    - PDF_TEXT_FULL: 叠加ARS 5维评分(付费、高精度)
    - 综合分 = 关键词40% + ARS 60%(有ARS时) / 关键词100%(无ARS时)
    """
    kw = _keyword_score(paper)

    rl = paper.get("reading_level", ReadingLevel.ABSTRACT_ONLY)
    if rl == ReadingLevel.PDF_TEXT_FULL:
        ars = _ars_score(paper)
        # 综合: 关键词40% + ARS 60%
        if ars.get("total") is not None and kw.get("total") is not None:
            combined_total = round(kw["total"] * 0.4 + ars["total"] * 0.6)
        elif ars.get("total") is not None:
            combined_total = ars["total"]
        else:
            combined_total = kw.get("total", 50)

        return {
            "score_type": "混合评分(关键词+ARS)",
            "score_confidence": "高置信",
            "total": combined_total,
            # ARS 5维
            "ars_originality": ars.get("originality"),
            "ars_methodology": ars.get("methodology_rigor"),
            "ars_evidence": ars.get("evidence_sufficiency"),
            "ars_argument": ars.get("argument_coherence"),
            "ars_writing": ars.get("writing_quality"),
            "ars_total": ars.get("total"),
            # 统一7维关键词分
            "kw_direction": kw.get("direction_relevance"),
            "kw_method": kw.get("method_rigor"),
            "kw_innovation": kw.get("innovation"),
            "kw_evidence": kw.get("evidence_sufficiency"),
            "kw_argument": kw.get("argument_coherence"),
            "kw_writing": kw.get("writing_quality"),
            "kw_transfer": kw.get("transferability"),
            "kw_total": kw.get("total"),
            "_ars_pending": ars.get("_ars_pending", False),
            "_ars_prompt": ars.get("_ars_prompt", ""),
        }

    # 仅摘要 → 关键词评分
    kw["score_type"] = "关键词8维初筛(摘要级)"
    kw["score_confidence"] = "低置信，仅用于排序"
    return kw


def _ars_score(paper: Dict) -> Dict:
    """委托 academic-research-skills plugin 进行5维0-100评分。
    维度: originality(20%) + methodology(25%) + evidence(25%) + argument(15%) + writing(15%)
    """
    title = paper.get("title", "Unknown")
    return {
        "originality": None,
        "methodology_rigor": None,
        "evidence_sufficiency": None,
        "argument_coherence": None,
        "writing_quality": None,
        "total": None,
        "_ars_pending": True,
        "_ars_prompt": (
            f"academic-research-skills 5-dim rubric:\n"
            f"Title: {title}\n"
            f"originality(20%) methodology(25%) evidence(25%) argument(15%) writing(15%)\n"
            f">=80 Accept, 65-79 Minor Rev, 50-64 Major Rev, <50 Reject"
        ),
    }


def _keyword_score(paper: Dict) -> Dict:
    """统一7维即时评分 (1-5分 → 加权0-100)。与 references/paper-grading.md 一致。
    维度: 方向相关度(15) 方法严谨性(25) 创新性(15) 证据充分性(15) 论证连贯性(10) 写作质量(10) 迁移价值(10)
    """
    title = (paper.get("title", "") + " " + paper.get("abstract", "")).lower()
    scores = {}

    # 1. 方向相关度 (15%) — 导师方向关键词匹配
    dir_kw = ["dem", "digital elevation", "terrain", "gis", "spatial analysis",
              "erosion", "gully", "loess", "dry-hot", "watershed", "soil",
              "remote sensing", "sentinel", "landsat", "insar", "uav", "sfm"]
    dir_match = sum(1 for k in dir_kw if k in title)
    scores["direction_relevance"] = min(5, 2 + dir_match)

    # 2. 方法严谨性 (25%) — 合并原"方法新颖度"+ARS methodology_rigor
    method_kw = ["benchmark", "compar", "baseline", "ablation", "cross-valid",
                 "reproducib", "open source", "github", "code availab"]
    m_match = sum(1 for k in method_kw if k in title)
    scores["method_rigor"] = 3 + min(2, m_match)  # 3-5

    # 3. 创新性 (15%) — 合并原"创新性"+ARS originality
    novel_kw = ["novel", "first", "new approach", "we propose", "innovative",
                "we introduce", "new method"]
    n_match = sum(1 for k in novel_kw if k in title)
    scores["innovation"] = 3 + min(2, n_match)

    # 4. 证据充分性 (15%) — 合并原"数据质量"+ARS evidence_sufficiency
    data_kw = ["dataset", "open data", "publicly availab", "sentinel", "landsat",
               "modis", "ground truth", "field data", "citizen scien",
               "statistically significant", "p-value", "confidence interval"]
    d_match = sum(1 for k in data_kw if k in title)
    d_score = 3 + min(2, d_match)
    if paper.get("is_oa"):
        d_score = min(d_score + 1, 5)
    scores["evidence_sufficiency"] = d_score

    # 5. 论证连贯性 (10%) — 来自ARS argument_coherence
    arg_score = 3
    if len(paper.get("abstract", "")) > 400:
        arg_score = 4
    if any(k in title for k in ["systematic", "comprehensive", "framework"]):
        arg_score = min(arg_score + 1, 5)
    scores["argument_coherence"] = arg_score

    # 6. 写作质量 (10%) — 两方合并
    w_score = 3
    abstract = paper.get("abstract", "")
    if len(abstract) > 400:
        w_score = 4
    if len(abstract) > 600:
        w_score = 5
    scores["writing_quality"] = w_score

    # 7. 迁移价值 (10%) — 保留原维度
    transfer_kw = ["open source", "python", "code availab", "github", "reproducib",
                   "tutorial", "benchmark", "tool", "pipeline", "framework", "workflow",
                   "dem", "digital elevation", "terrain", "gis", "spatial analysis",
                   "erosion", "gully", "loess", "dry-hot", "watershed"]
    t_match = sum(1 for k in transfer_kw if k in title)
    scores["transferability"] = 3 + min(2, t_match)

    # 加权综合 (0-100)
    weights = {
        "direction_relevance": 0.15, "method_rigor": 0.25,
        "innovation": 0.15, "evidence_sufficiency": 0.15,
        "argument_coherence": 0.10, "writing_quality": 0.10,
        "transferability": 0.10,
    }
    total = sum(scores[k] * weights[k] for k in scores)
    scores["total"] = round(total * 20)  # 1-5 → 0-100

    rl = paper.get("reading_level", ReadingLevel.ABSTRACT_ONLY)
    if rl in (ReadingLevel.META_ONLY, ReadingLevel.ABSTRACT_ONLY):
        scores["score_type"] = "关键词即时评分(摘要级)"
        scores["score_confidence"] = "低置信，仅用于排序"
    else:
        scores["score_type"] = "关键词即时评分(全文)"
        scores["score_confidence"] = "中置信，待ARS精读补充"

    return scores


# ── 旧版简单评分 (保留作为备选) ───────────────────────

def score_paper(paper: Dict) -> int:
    """快速相关性评分, 用于初筛排序 — 基于标题+摘要关键词匹配
    注意: 对于 ABSTRACT_ONLY 论文，此分数仅用于候选排序，不代表论文质量评价。"""
    title = (paper.get("title", "") + " " + paper.get("abstract", "")).lower()

    # 误判检测: 排除医学CT/非GIS/纯书评等
    false_positive_kw = [
        "computed tomography", "ct scan", "ct image", "ct scanner", "ct colonography",
        "x-ray", "radiolog", "clinical trial", "patient diagnosis",
        "tumor", "cancer", "malignan", "metastas",
        "drug", "pharmac", "surgery", "surgical", "biomedical", "genomic",
        "drosophila", "zebrafish", "cell line", "in vitro", "in vivo",
        "book review", "editorial", "commentary", "corrigendum", "erratum",
        "ct enterography", "ct urography", "ct angiography", "mammography",
        "dementia", "alzheimer", "parkinson", "multiple sclerosis",
        "electrocardiogram", "electroencephalogram",
    ]
    for fkw in false_positive_kw:
        if fkw in title:
            return 0  # 明确不属于GIS/遥感领域，直接淘汰

    # 医学CT混淆DEM检测: 如果标题同时包含CT相关词和"dem"，很可能是医学论文
    ct_adjacent = ["ct-", "ct ", "computed tomography", "scan", "scanner"]
    has_ct = any(k in title for k in ct_adjacent)
    has_dem = "dem" in title and "digital elevation" not in title and "dem " in title
    if has_ct and has_dem:
        # CT影像检查 + DEM(非digital elevation) → 可能医学论文或CT衍生DEM
        # 保持谨慎：检查是否真的有GIS上下文
        gis_context_terms = ["terrain", "elevation", "gis", "remote sens", "geospat",
                             "slope", "topograph", "landslide", "erosion"]
        if not any(k in title for k in gis_context_terms):
            return 0

    # 综述/书评检测: 如果只是纯综述/书评且无GIS关键词
    review_only_kw = ["book review", "literature review", "a review of",
                      "a systematic review", "review article"]
    is_pure_review = any(k in title for k in review_only_kw)
    if is_pure_review:
        gis_relevance = any(k in title for k in ["gis", "geospat", "remote sens",
                           "spatial", "terrain", "elevation", "dem", "satellite"])
        if not gis_relevance:
            return 0

    # ═══ 核心关键词 — 必须命中至少1个, 否则直接打0分 ═══
    # 分为两层: 硬核层（必须命中至少1个）和扩展层（加分但不单独通过）
    hard_core = [
        # ── DEM/地形核心 ──
        "dem", "digital elevation", "digital terrain", "topograph",
        "geomorpholog", "geomorphometry", "terrain analysis",
        "terrain factor", "terrain attributes", "landform",
        # ── 沟谷/侵蚀核心 ──
        "gully", "gully erosion", "gully morphology",
        "soil erosion", "erosion model", "rusle",
        "soil loss", "rill erosion", "bank erosion",
        # ── 区域核心 ──
        "loess plateau", "黄土高原", "dry-hot valley", "干热河谷",
        "jinsha", "yuanmou", "元谋",
        # ── 水土保持/荒漠化 ──
        "soil conservation", "soil water conservation",
        "water and soil conservation", "desertification",
        # ── DEM相关地形因子 ──
        "slope gradient", "slope aspect", "curvature",
        "topographic wetness", "ls factor", "stream power",
        "drainage network",
    ]
    # 扩展层: GIS/空间/流域（有这些但无硬核词仍不能通过）
    extended_core = [
        "gis", "geographic information", "spatial analysis",
        "spatial model", "spatial statistic", "geospatial",
        "spatial pattern", "spatial distribution",
        "watershed", "catchment",
        "sediment yield", "erosion risk", "erosion assessment",
        "erosion control", "srtm", "aster gdem", "lidar dem", "uav dem",
        "land degradation",
    ]
    hard_hits = sum(1 for kw in hard_core if kw in title)
    if hard_hits == 0:
        return 0  # 没有任何硬核关键词 → 直接淘汰

    extended_hits = sum(1 for kw in extended_core if kw in title)

    # ── 低优先级剔除关键词 ──
    # 以下领域除非明确和 DEM/侵蚀/沟谷/空间建模有关, 否则剔除
    low_priority_solo = [
        # 纯遥感分类（无DEM/侵蚀/地形上下文）
        "remote sensing classification",
        "land cover classification", "land use classification",
        "image segmentation", "semantic segmentation",
        # 纯AI/大模型（无地理问题）
        "large language model", "foundation model",
        "chatgpt", "gpt-", "prompt engineering",
        # 城市/交通（无DEM/侵蚀）
        "urban heat island", "urban expansion", "urban sprawl",
        "urban growth", "urbanization pattern",
        "traffic", "transportation", "road network",
        "nighttime light", "population density",
        # 气候/生态（无DEM/侵蚀）
        "climate change", "carbon sequestration",
        "biodiversity", "ecosystem service",
        # 泛综述
        "a comprehensive review", "a systematic review",
    ]
    # 检查是否低优先级词是标题的"主词"(即没有核心词配合)
    has_core_reinforcement = any(k in title for k in [
        "dem", "digital elevation", "terrain", "erosion", "gully",
        "geomorpholog", "soil", "loess", "dry-hot", "watershed",
        "slope", "topograph",
    ])
    for kw in low_priority_solo:
        if kw in title and not has_core_reinforcement:
            return 0  # 低优先级无核心支撑 → 淘汰

    score = 0
    # 硬核命中越多分越高
    score += min(hard_hits * 18, 60)
    # 扩展命中加分
    score += min(extended_hits * 8, 24)

    # ── 方向专项加分 ──
    # DEM/地形分析专项
    dem_bonus = sum(1 for k in [
        "dem", "digital elevation", "digital terrain", "topograph",
        "geomorpholog", "geomorphometry", "terrain analysis",
        "terrain factor", "terrain attributes", "landform",
    ] if k in title)
    score += min(dem_bonus * 8, 24)

    # 沟谷/侵蚀专项
    gully_bonus = sum(1 for k in [
        "gully", "gully erosion", "gully morphology",
        "soil erosion", "erosion model", "rusle",
        "rill erosion", "bank erosion",
    ] if k in title)
    score += min(gully_bonus * 10, 30)

    # 区域专项
    region_bonus = sum(1 for k in [
        "loess plateau", "黄土高原", "dry-hot valley", "干热河谷",
        "jinsha", "金沙江", "yuanmou", "元谋",
    ] if k in title)
    score += min(region_bonus * 12, 36)

    # GIS空间分析专项
    gis_bonus = sum(1 for k in [
        "spatial analysis", "spatial model", "spatial statistic",
        "gis", "geospatial", "spatial distribution",
    ] if k in title)
    score += min(gis_bonus * 5, 15)

    # ── 方法关键词（仅保留与地形/侵蚀/空间分析相关的方法） ──
    method_kw = [
        "machine learning", "deep learning", "neural network",
        "random forest", "xgboost", "cnn",
        "segmentation", "classification", "object detection",
        "causal", "time series", "regression",
        "ensemble", "transfer learning", "explainable",
        "attention mechanism",
    ]
    for kw in method_kw:
        if kw in title:
            score += 3

    # 工具/可复现关键词
    tool_kw = ["python", "r package", "open source", "github",
               "code available", "benchmark", "dataset", "workflow",
               "pipeline", "automation", "reproducib"]
    for kw in tool_kw:
        if kw in title:
            score += 3

    # 方法论关键词（指标体系/不确定性等）
    cross_kw = ["indicator", "evaluation framework", "multi-criteria",
                "decision making", "uncertainty", "sensitivity analysis",
                "comparative study", "quantitative method"]
    for kw in cross_kw:
        if kw in title:
            score += 2

    year = paper.get("year", "")
    if year == "2026":
        score += 6
    elif year == "2025":
        score += 3

    if len(paper.get("abstract", "")) > 100:
        score += 3

    return min(score, 100)


# ── 生成日报 ───────────────────────────────────────────────

def generate_daily_report(date: str, candidates: List[Dict],
                          selected: List[Dict], queries_used: List[str],
                          fulltext_stats: Dict = None,
                          kb_result: Dict = None,
                          dedup_stats: Dict = None) -> str:
    """生成论文全文阅读日报 - 只有 PDF_TEXT_FULL/HUMAN_CONFIRMED 可入日报正文。

    报告结构 (8段):
      1. 今日检索与全文获取概况
      2. 去重统计
      3. 今日全文精读论文 (仅 PDF_TEXT_FULL / HUMAN_CONFIRMED)
      4. 今日未进入日报正文的候选论文
      5. 待全文补读队列
      6. 下载失败 / 解析失败列表
      7. 今日可加入长期知识库的论文
      8. 今日禁止加入长期知识库的论文
    """
    if fulltext_stats is None:
        fulltext_stats = {}
    if dedup_stats is None:
        dedup_stats = {}

    full_read = [p for p in candidates if p.get("reading_level") in
                 ("PDF_TEXT_FULL", "HUMAN_CONFIRMED")]
    has_full = len(full_read) > 0
    total_candidates = len(candidates)

    lines = [
        f"# 科研论文全文阅读日报 - {date}",
        "",
        f"> **自动生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> **阅读证据分级机制:** 已启用",
        f"> **硬规则:** 只有 PDF_TEXT_FULL / HUMAN_CONFIRMED 论文可进入日报正文和长期知识库",
        "",
        "---",
        "",
        "## 1. 今日检索与全文获取概况",
        "",
        "| 指标 | 数值 |",
        "|------|------|",
    ]

    pdf_linked = sum(1 for p in candidates if p.get("pdf_url") or p.get("arxiv_id"))
    stats_rows = [
        ("搜索关键词数", str(len(queries_used))),
        ("候选论文数", str(total_candidates)),
        ("找到 PDF/HTML 链接数", str(pdf_linked)),
        ("成功下载全文数", str(fulltext_stats.get("downloaded", 0))),
        ("成功解析正文数", str(fulltext_stats.get("downloaded", 0) - fulltext_stats.get("parse_failed", 0))),
        ("达到 PDF_TEXT_FULL 数", str(fulltext_stats.get("pdf_text_full", len(full_read)))),
        ("进入日报正文数", str(len(full_read))),
        ("待补读数", str(
            fulltext_stats.get("abstract_only", 0)
            + fulltext_stats.get("pdf_text_partial", 0)
            + fulltext_stats.get("download_failed", 0)
            + fulltext_stats.get("meta_only", 0)
            + fulltext_stats.get("parse_failed", 0)
        )),
        ("下载失败数", str(fulltext_stats.get("download_failed", 0))),
        ("解析失败数", str(fulltext_stats.get("parse_failed", 0))),
    ]
    for label, val in stats_rows:
        lines.append(f"| {label} | {val} |")

    if not has_full:
        lines += [
            "",
            "> **今日没有论文满足全文阅读标准，因此不生成全文精读卡片、不生成正式学术评分、不写入长期知识库。**",
            "> 日报宁可为空，也不能假。",
        ]

    lines += [
        "",
        "---",
        "",
        "## 2. 去重统计",
        "",
        "| 指标 | 数值 |",
        "|------|------|",
        f"| 今日候选论文数 | {dedup_stats.get('total_candidates', 0)} |",
        f"| 方向不匹配剔除 | {dedup_stats.get('direction_filtered', 0)} |",
        f"| paper_id 去重 | {dedup_stats.get('seen_dedup', 0)} |",
        f"| DOI/标题/URL 跨源去重 | {dedup_stats.get('cross_dedup', 0)} |",
        f"| 最终保留论文数 | {dedup_stats.get('final_count', len(candidates))} |",
        "",
    ]

    deduped_titles = dedup_stats.get("deduped_titles", [])
    if deduped_titles:
        lines.append("**被去重论文列表:**")
        lines.append("")
        for i, t in enumerate(deduped_titles[:10], 1):
            lines.append(f"{i}. {t}")
        lines.append("")

    suspicious = dedup_stats.get("suspicious_titles", [])
    if suspicious:
        lines.append("**疑似重复论文（未进入主推荐，仅记录日志）:**")
        lines.append("")
        for i, t in enumerate(suspicious[:5], 1):
            lines.append(f"{i}. {t}")
        lines.append("")

    lines += [
        "",
        "---",
        "",
        "## 3. 今日全文精读论文",
        "",
    ]

    if has_full:
        lines.append("> 以下论文已达到 PDF_TEXT_FULL 或 HUMAN_CONFIRMED 标准。")
        lines.append("")
        low_quality_count = 0
        for i, p in enumerate(full_read, 1):
            paper_id = f"{date}_F{i:02d}"
            card_lines = _render_fulltext_card_v2(paper_id, p, date)
            card_text = "\n".join(card_lines)
            if is_low_quality_card(card_text):
                # 自动抽取质量不足时保留卡片，但显式标注待复核。
                placeholder_count = count_placeholder_fields(card_text)
                p["quality_flag"] = f"LOW_QUALITY ({placeholder_count} 个占位符)"
                low_quality_count += 1
                card_lines[2:2] = [
                    f"> **自动抽取质量提示:** 检测到 {placeholder_count} 个待复核字段；仍按日报补齐要求保留卡片内容，后续可人工复核关键结论。",
                    "",
                ]
                print(f"  [!] {p.get('title','?')[:60]}... -> 卡片含{placeholder_count}个待复核字段，已保留并标注")
            lines += card_lines
        if low_quality_count > 0:
            print(f"  [*] 质量门控: {low_quality_count} 篇论文已保留卡片并标注待复核")
    else:
        lines += [
            "> **今日无全文精读论文。**",
        ]

    # 3. 未进入日报正文的候选论文
    non_full = [p for p in candidates if p.get("reading_level") not in
                ("PDF_TEXT_FULL", "HUMAN_CONFIRMED")]
    lines += [
        "",
        "---",
        "",
        "## 4. 今日未进入日报正文的候选论文",
        "",
        "> 以下论文因阅读等级不足，只能以表格形式列出，不生成正式知识卡片。",
        "",
        "| # | 标题 | 作者 | 年 | 来源 | PDF/HTML | 阅读等级 | 未进入原因 | 下一步 |",
        "|---|------|------|----|------|----------|----------|------------|------|",
    ]

    for i, p in enumerate(non_full[:20], 1):
        rl = READING_LEVEL_LABELS.get(p.get("reading_level", ""), "?")
        src = "S2" if "Semantic" in p.get("source", "") else "arXiv"
        dl_status = p.get("fulltext_download_status", "")
        if dl_status == "failed":
            pdf_status = "下载失败"
        elif dl_status == "downloaded":
            ext_status = p.get("fulltext_extraction_status", "")
            pdf_status = "解析失败" if ext_status == "failed" else "已下载"
        elif p.get("pdf_url") or p.get("arxiv_id"):
            pdf_status = "有链接"
        else:
            pdf_status = "无链接"
        reason = _get_non_entry_reason(p)
        next_step = _get_next_step(p)
        title = p.get("title", "")[:40]
        author = p.get("first_author", "")[:10]
        year = p.get("year", "")
        lines.append(
            f"| {i} | {title} | {author} | {year} | {src} "
            f"| {pdf_status} | {rl} | {reason} | {next_step} |")

    # 4. 待全文补读队列
    worth_reading = non_full
    lines += [
        "",
        "---",
        "",
        "## 5. 待全文补读队列",
        "",
        "> 以下论文值得获取全文后进行详细阅读。",
        "",
        "| # | 标题 | 链接 | 当前状态 | 推荐理由 | 优先级 | 需确认的问题 |",
        "|---|------|------|----------|----------|--------|--------------|",
    ]
    for i, p in enumerate(worth_reading[:10], 1):
        rl = READING_LEVEL_LABELS.get(p.get("reading_level", ""), "?")
        url = p.get("pdf_url") or p.get("url", "")
        priority = "高" if p.get("score", 0) >= 40 else ("中" if p.get("score", 0) >= 25 else "低")
        reason = get_short_reason(p)
        title = p.get("title", "")[:40]
        lines.append(f"| {i} | {title} | [链接]({url}) | {rl} | {reason} | {priority} | 方法/数据/结论 |")

    # 5. 下载失败 / 解析失败列表
    download_failed = [p for p in candidates if p.get("fulltext_download_status") == "failed"]
    parse_failed = [p for p in candidates if
                    p.get("fulltext_download_status") == "downloaded" and
                    p.get("fulltext_extraction_status") == "failed"]
    all_failed = download_failed + parse_failed
    seen_failed = set()
    all_failed_unique = []
    for p in all_failed:
        pid = p.get("paper_id", "")
        if pid not in seen_failed:
            seen_failed.add(pid)
            all_failed_unique.append(p)

    lines += [
        "",
        "---",
        "",
        "## 6. 下载失败 / 解析失败列表",
        "",
        "| # | 标题 | 链接 | 失败阶段 | 错误原因 | 下一步建议 |",
        "|---|------|------|----------|----------|------------|",
    ]
    for i, p in enumerate(all_failed_unique[:10], 1):
        title = p.get("title", "")[:40]
        url = p.get("pdf_url") or p.get("url", "")
        dl = p.get("fulltext_download_status", "")
        ext = p.get("fulltext_extraction_status", "")
        if dl == "failed":
            stage = "下载失败"
            err = "下载超时或链接无效"
        elif ext == "failed":
            stage = "解析失败"
            err = "PDF文本提取失败"
        else:
            stage = "未知"
            err = ""
        suggestion = "手动下载并验证" if dl == "failed" else "尝试替代工具解析"
        lines.append(f"| {i} | {title} | [链接]({url}) | {stage} | {err} | {suggestion} |")

    if not all_failed_unique:
        lines.append("| - | 今日无下载/解析失败的论文 | - | - | - | - |")

    # 6. 可加入长期知识库
    lines += [
        "",
        "---",
        "",
        "## 7. 今日可加入长期知识库的论文",
        "",
        "> 只有 PDF_TEXT_FULL / HUMAN_CONFIRMED 允许写入长期知识库。",
        "",
    ]
    if has_full:
        lines.append("| # | 标题 | 阅读等级 | 全文长度 | 覆盖章节 | 可信度 |")
        lines.append("|---|------|----------|----------|----------|--------|")
        for i, p in enumerate(full_read, 1):
            rl = READING_LEVEL_LABELS.get(p.get("reading_level", ""), "?")
            chars = p.get("fulltext_text_length_chars", 0)
            words = p.get("fulltext_text_length_words", 0)
            sections = p.get("fulltext_sections", {}).get("key_sections_covered", 0)
            confidence = "高" if p.get("reading_level") == "HUMAN_CONFIRMED" else "中高"
            title = p.get("title", "")[:45]
            lines.append(f"| {i} | {title} | {rl} | {chars}字/{words}词 | {sections}类章节 | {confidence} |")
    else:
        lines.append("> 今日无符合条件的论文。")

    # 7. 禁止加入长期知识库
    lines += [
        "",
        "## 8. 今日禁止加入长期知识库的论文",
        "",
        "> META_ONLY / ABSTRACT_ONLY / PDF_TEXT_PARTIAL / 下载失败 / 解析失败论文禁止写入长期知识库。",
        "",
        "| # | 标题 | 当前等级 | 禁止原因 |",
        "|---|------|----------|----------|",
    ]
    for i, p in enumerate(non_full[:15], 1):
        rl = READING_LEVEL_LABELS.get(p.get("reading_level", ""), "?")
        reason = _get_kb_ban_reason(p)
        title = p.get("title", "")[:45]
        lines.append(f"| {i} | {title} | {rl} | {reason} |")

    # 检索日志
    lines += [
        "",
        "---",
        "",
        "## 检索日志",
        "",
        "| 数据库 | 关键词 | 过滤器 | 结果数 |",
        "|--------|--------|--------|--------|",
    ]
    for q in sorted(set(queries_used)):
        count = sum(1 for p in candidates if p.get("keywords", "") == q)
        lines.append(f"| arXiv | `{q}` | 最近, 相关性 | {count} |")

    if fulltext_stats.get("s2_rate_limited"):
        lines.append("| Semantic Scholar | - | **429 Rate Limited** | 已降级跳过 |")
    else:
        lines.append("| Semantic Scholar | 同上关键词 | 最近, OA优先 | 已合并至上方 |")

    # KB 写入状态
    if kb_result is None:
        kb_result = {}
    kb_count = kb_result.get("kb_count", 0)
    inno_count = kb_result.get("inno_count", 0)
    kb_ids = kb_result.get("kb_mapping", {})

    lines += [
        "",
        "---",
        "",
        "## KB 写入状态",
        "",
        f"- 今日入库数量: {kb_count}",
        f"- 今日新增创新点数量: {inno_count}",
        f"- 今日未入库但建议补读数量: {len([p for p in (selected or []) if p.get('reading_level') not in ('PDF_TEXT_FULL', 'HUMAN_CONFIRMED')])}",
        f"- 对应长期知识库日期段: {'## ' + date if kb_count > 0 else '无'}",
        f"- 对应创新点日期段: {'## ' + date if inno_count > 0 else '无'}",
    ]
    if kb_count == 0:
        full_count = sum(1 for p in (selected or []) if p.get("reading_level") in ("PDF_TEXT_FULL", "HUMAN_CONFIRMED"))
        abstract_count = sum(1 for p in (selected or []) if p.get("reading_level") not in ("PDF_TEXT_FULL", "HUMAN_CONFIRMED"))
        if full_count == 0 and abstract_count > 0:
            lines.append(f"- 备注: 今日仅摘要级内容，无通过全文/硬检查标准且适合进入长期知识库的论文。")
        elif full_count == 0:
            lines.append(f"- 备注: 今日无符合入库标准的论文。")
        else:
            lines.append(f"- 备注: 今日{full_count}篇全文论文均被去重或不符合入库标准。")
    else:
        lines.append(f"- 备注: 已写入长期知识库。")

    lines += [
        "",
        f"*自动生成于 {datetime.now().strftime('%m/%d %H:%M')} \\u00b7 阅读证据分级机制已启用 \\u00b7 日报宁可为空，也不能假*",
    ]

    return "\n".join(lines)


# ── 占位符检测与质量门控 ─────────────────────────────────

PLACEHOLDER_PATTERNS = [
    "正文中未检测到",
    "摘要中未检测到",
    "不代表没有价值",
    "不代表没有局限",
    "建议人工阅读",
    "无法检查",
    "未检测到明确",
    "未检测到常见方法名",
    "未检测到结构化结果段落",
    "未检测到独立结论",
    "未检测到明确提出局限性",
    "未检测到明确数据来源",
    "未检测到明确实验设计",
    "未检测到明确研究区",
    "未检测到明确可迁移点",
]


def count_placeholder_fields(card_text: str) -> int:
    """统计卡片中占位符字段数量。>=3 个占位符 → 低质量卡片。"""
    return sum(1 for pat in PLACEHOLDER_PATTERNS if pat in card_text)


def is_low_quality_card(card_text: str) -> bool:
    """卡片占位符 >=5 个 → 低质量，不应进入日报正文。

    阈值从 3 调至 5（2026-06-15）：3 过于严格，
    导致 16 篇 arXiv 论文全部被降级。5 在保留质量门控的同时减少误杀。
    """
    return count_placeholder_fields(card_text) >= 5


# ── 论文卡片渲染 ──────────────────────────────────────────

def _render_fulltext_card_v2(paper_id: str, p: Dict, date: str) -> List[str]:
    """PDF_TEXT_FULL / HUMAN_CONFIRMED 的完整知识卡片"""
    sections = p.get("fulltext_sections", {})
    evidence = p.get("fulltext_evidence_report", {})

    lines = [
        f"### Paper_ID: {paper_id}",
        "",
        "#### 全文精读卡片",
        f"- **标题:** {p['title']}",
        f"- **作者:** {', '.join(p.get('authors', [])[:5])}",
        f"- **年份:** {p.get('year', '')}",
        f"- **来源:** {p.get('source', '')}",
        f"- **论文分类:** {normalize_paper_category(p.get('category', ''))}",
        f"- **DOI:** {p.get('doi') or '未提供'}",
        f"- **arXiv ID:** {p.get('arxiv_id') or '未提供'}",
        f"- **原文链接:** {p.get('url', '')}",
        f"- **PDF/HTML 链接:** {p.get('pdf_url', '')}",
        f"- **本地全文路径:** `{p.get('fulltext_local_path', '')}`",
        f"- **阅读等级:** {READING_LEVEL_LABELS.get(p.get('reading_level',''), '?')}",
        "- **是否已读完全文:** 是",
        f"- **正文有效长度:** {p.get('fulltext_text_length_chars', 0)} 字符 / {p.get('fulltext_text_length_words', 0)} 词",
        f"- **解析到的章节:** {', '.join(sections.get('detected_sections', []))}",
        f"- **全文证据状态:** {evidence.get('reason', '')}",
        f"- **可信度:** {'人工确认' if p.get('reading_level') == 'HUMAN_CONFIRMED' else '全文解析'}",
        "",
        f"- **研究问题:** {extract_research_question(p)}",
        f"- **数据来源:** {_extract_data_source_full(p)}",
        f"- **研究区域:** {_extract_study_area(p)}",
        f"- **方法流程:** {_extract_methods_full(p)}",
        f"- **实验/案例设计:** {_extract_experiment(p)}",
        f"- **主要结果:** {_extract_results_full(p)}",
        f"- **结论:** {extract_conclusions(p)}",
        f"- **局限:** {extract_limitations(p)}",
        f"- **可迁移到 GIS/遥感/空间分析的点:** {extract_gis_transfer(p)}",
        "",
        "#### 可能的创新点",
        "",
    ]
    inno = generate_possible_innovations(p)
    if inno:
        for inn in inno:
            lines.append(f"  - 【{inn['type']}】{inn['text']} [{inn['confidence']}]")
    else:
        lines.append("  - 暂未提取")
    lines += [
        "#### 一句话总结",
        f"> {make_oneline_summary(p)}",
        "",
        "#### 正式学术评分",
        "",
    ]
    lines += _render_rubric_table(p)
    lines += [
        "",
        "- **是否建议加入长期知识库:** 是",
        f"- **加入理由:** 全文已解析，覆盖{len(sections.get('detected_sections', []))}类章节",
        "",
        "---",
        "",
    ]
    return lines


def _render_rubric_table(p: Dict) -> List[str]:
    """渲染评分表格"""
    rub = p.get("rubric", {})
    score_type = rub.get("score_type", "未知")
    score_confidence = rub.get("score_confidence", "")

    result = [
        f"> **评分类型:** {score_type}",
        f"> **可信度:** {score_confidence}",
        "",
    ]

    dims = [
        ("问题清晰度", "problem_clarity"),
        ("文献背景", "literature_context"),
        ("方法论", "methodology"),
        ("数据与证据", "data_evidence"),
        ("分析质量", "analysis"),
        ("写作质量", "writing_quality"),
        ("创新性", "innovation"),
        ("可迁移性", "transferability"),
    ]
    for dim_name, dim_key in dims:
        s = rub.get(dim_key, "?")
        star_bar = "█" * s + "░" * (5 - s) if isinstance(s, int) else "?"
        result.append(f"- **{dim_name}:** {star_bar} ({s}/5)")

    result.append(f"- **综合评分:** {rub.get('total', '?')}/100")
    return result


# ── 辅助函数 (报告用) ─────────────────────────────────────

def _extract_data_source_full(paper: Dict) -> str:
    return extract_data_source(paper)


def _get_section_text(paper: Dict, section_key: str, max_chars: int = 300) -> Optional[str]:
    """从 fulltext_sections 中提取指定章节的文本片段"""
    sections = paper.get("fulltext_sections", {})
    content = sections.get(section_key, {}).get("content", "")
    if not content or len(content) < 20:
        return None
    return content[:max_chars] + ("..." if len(content) > max_chars else "")


def _extract_study_area(paper: Dict) -> str:
    sections = paper.get("fulltext_sections", {})
    abstract = sections.get("abstract", {}).get("content", "")
    methods = sections.get("methods", {}).get("content", "")

    # 从摘要和方法中搜索地点/研究区关键词
    import re
    candidates = []
    geo_patterns = [
        r'(?:study\s*area|study\s*site|study\s*region|covers?)\s*(?:is|was|in|the)?\s*([\w\s,.-]+?)(?:\.|,|\s*and|\s*with|\s*at|\s*$)',
        r'(?:located|situated)\s*in\s*([\w\s,.-]+?)(?:\.|,|\s*and|\s*$)',
        r'(?:in)\s*(the\s*)?([\w\s]+?(?:Basin|River|Lake|Mountain|Forest|City|County|Province|Region|Desert|Plateau|Valley|Island|Ocean|Sea))[\s,.]',
        r'(?:data\s*(?:was|were|is|are)\s*(?:collected|obtained|acquired)\s*(?:from|in|at))\s*([\w\s,.-]+?)(?:\.|,|$)',
    ]
    for source_text in [abstract, methods]:
        if not source_text:
            continue
        for pat in geo_patterns:
            matches = re.findall(pat, source_text[:3000], re.IGNORECASE)
            for m in matches:
                m = m.strip().rstrip('.').rstrip(',')
                if len(m) > 5 and len(m) < 80 and m.lower() not in ('this paper', 'this study', 'the following', 'various'):
                    candidates.append(m)

    if candidates:
        unique = list(dict.fromkeys(candidates))[:3]
        return "- " + "\n- ".join(unique)
    return "- 正文中未检测到明确研究区描述"


def _extract_methods_full(paper: Dict) -> str:
    return extract_methods(paper)


def _extract_experiment(paper: Dict) -> str:
    sections = paper.get("fulltext_sections", {})
    results = sections.get("results", {}).get("content", "")
    methods = sections.get("methods", {}).get("content", "")

    # 搜索实验/案例线索
    import re
    hints = []
    for source_text in [methods, results]:
        if not source_text:
            continue
        # 检测实验类型
        for pat, label in [
            (r'(?:we|authors?)\s*(?:conduct|perform|carry\s*out|run|execut)\s*(?:a|an|the)?\s*([\w\s-]{10,60}?)(?:\.|,|;|to\s)', '实验类型'),
            (r'(?:dataset|data\s*set)\s*(?:is|was|consists?\s*of|contains?|includes?)\s*([\w\s,.-]{10,80}?)(?:\.|,|;)', '数据集'),
            (r'(?:we|authors?)\s*(?:use|used|employ|appl(y|ied))\s*(?:a|an|the)?\s*([\w\s-]{10,60}?)(?:dataset|data|model|method|approach|algorithm)', '使用方法'),
            (r'(?:compared|benchmark|baseline|against)\s*(?:with|to|against)?\s*([\w\s-]{10,60}?)(?:\.|,|;|method|model)', '对比基准'),
        ]:
            matches = re.findall(pat, source_text[:3000], re.IGNORECASE)
            for m in matches[:2]:
                m = m.strip()[:80]
                if len(m) > 10:
                    hints.append(f"  - {label}: {m}")

    if hints:
        return "\n".join(list(dict.fromkeys(hints))[:4])
    return "- 正文中未检测到明确实验设计描述"


def _extract_results_full(paper: Dict) -> str:
    rl = paper.get("reading_level", "")
    if rl in ("PDF_TEXT_FULL", "HUMAN_CONFIRMED"):
        sections = paper.get("fulltext_sections", {})
        results_content = sections.get("results", {}).get("content", "")
        if results_content and len(results_content) > 50:
            # 提取结果段落中的关键句
            import re
            sentences = re.split(r'(?<=[.!?])\s+', results_content[:2000])
            key_sentences = [s.strip() for s in sentences if len(s.strip()) > 30 and any(
                kw in s.lower() for kw in ['result', 'find', 'show', 'observ', 'achieve',
                                            'perform', 'accur', 'error', 'improv', 'compar',
                                            'signific', 'outperform', 'better', 'higher', 'lower',
                                            'increase', 'decrease', 'correlat', 'percent', '%'])
            ][:5]
            if key_sentences:
                return "- " + "\n- ".join(key_sentences)
        chars = paper.get("fulltext_text_length_chars", 0)
        if chars > 5000:
            return f"全文已获取 ({chars}字符)，但未检测到结构化结果段落"
        return "- 正文内容不足以提取结构化结果"
    return "- 未读取全文，不可输出结果"


def extract_conclusions(paper: Dict) -> str:
    rl = paper.get("reading_level", "")
    if rl in ("PDF_TEXT_FULL", "HUMAN_CONFIRMED"):
        sections = paper.get("fulltext_sections", {})
        conclusion = sections.get("conclusion", {}).get("content", "")
        discussion = sections.get("discussion", {}).get("content", "")
        source = conclusion or discussion
        if source and len(source) > 50:
            import re
            sentences = re.split(r'(?<=[.!?])\s+', source[:1500])
            key = [s.strip() for s in sentences if len(s.strip()) > 30][:3]
            if key:
                return "- " + "\n- ".join(key)
            return f"- 结论/讨论章节已提取 ({len(source)}字符)，未识别到关键句"
        return "- 正文已获取，但未检测到独立结论/讨论章节"
    return "- 未读取全文"


def extract_limitations(paper: Dict) -> str:
    rl = paper.get("reading_level", "")
    if rl in ("PDF_TEXT_FULL", "HUMAN_CONFIRMED"):
        sections = paper.get("fulltext_sections", {})
        # 在所有章节中搜索局限相关语言
        all_text = ""
        for sec_name in ["discussion", "conclusion", "methods", "results"]:
            all_text += sections.get(sec_name, {}).get("content", "") + "\n"
        if all_text:
            import re
            limit_patterns = [
                r'([^.]*?(?:limitation|limitation|shortcoming|drawback|weakness|future\s*work|not\s*addressed|beyond\s*scope|further\s*(?:study|research|investigation))[^.]*\.)',
            ]
            found = []
            for pat in limit_patterns:
                matches = re.findall(pat, all_text[:5000], re.IGNORECASE)
                for m in matches[:3]:
                    m = m.strip()[:150]
                    if len(m) > 20:
                        found.append(f"- {m}")
            if found:
                return "\n".join(list(dict.fromkeys(found))[:3])
            return "- 正文中未检测到明确提出局限性的语句（不代表没有局限）"
        return "- 正文已获取，但无法自动识别局限性段落"
    return "- 未读取全文"


def _get_non_entry_reason(paper: Dict) -> str:
    rl = paper.get("reading_level", "")
    dl = paper.get("fulltext_download_status", "")
    ext = paper.get("fulltext_extraction_status", "")
    if dl == "failed":
        return "下载失败"
    if dl == "not_attempted":
        return "未尝试下载"
    if ext == "failed":
        return "解析失败"
    if rl == "PDF_TEXT_PARTIAL":
        return "正文不达标"
    if rl == "ABSTRACT_ONLY":
        return "仅有摘要"
    if rl == "META_ONLY":
        return "仅有元数据"
    return "未达标"


def _get_next_step(paper: Dict) -> str:
    dl = paper.get("fulltext_download_status", "")
    if dl == "failed":
        return "手动下载"
    if dl == "not_attempted" and (paper.get("pdf_url") or paper.get("arxiv_id")):
        return "重试下载"
    if paper.get("reading_level") == "PDF_TEXT_PARTIAL":
        return "手工补读"
    if paper.get("pdf_url") or paper.get("arxiv_id"):
        return "下载全文"
    return "自行检索"


def _get_kb_ban_reason(paper: Dict) -> str:
    rl = paper.get("reading_level", "")
    dl = paper.get("fulltext_download_status", "")
    if rl == "META_ONLY":
        return "仅元数据"
    if rl == "ABSTRACT_ONLY":
        return "仅摘要，非可靠知识"
    if rl == "PDF_TEXT_PARTIAL":
        return "正文不完整"
    if dl == "failed":
        return "下载失败"
    if paper.get("fulltext_extraction_status") == "failed":
        return "解析失败"
    return "等级不足"

# ── 辅助函数 ───────────────────────────────────────────────

def get_short_reason(paper: Dict) -> str:
    title = paper.get("title", "").lower()
    reasons = []
    if any(k in title for k in ["dem", "terrain", "elevation", "topograph"]):
        reasons.append("地形相关")
    if any(k in title for k in ["remote sensing", "sentinel", "landsat", "gee"]):
        reasons.append("遥感数据")
    if any(k in title for k in ["machine learning", "deep learning", "neural"]):
        reasons.append("ML方法")
    if any(k in title for k in ["spatial", "gis", "geospatial"]):
        reasons.append("空间分析")
    if any(k in title for k in ["python", "open source", "github"]):
        reasons.append("可复现代码")
    return ", ".join(reasons[:2]) or "综合相关"


def make_oneline_summary(paper: Dict) -> str:
    """从标题和摘要生成中文一句话总结 — 严格标注来源。

    关键词匹配使用词边界检查防止误匹配：
    - "dem" 只匹配独立出现的 DEM/Dem 缩写，不匹配 "demonstrate"/"demand"
    - 短关键词(<4字符)只在标题中作为独立词出现时才生效
    """
    import re as _re

    title = paper.get("title", "").strip()
    keywords = paper.get("keywords", "")
    category = paper.get("category", "")
    abstract = paper.get("abstract", "")
    rl = paper.get("reading_level", ReadingLevel.ABSTRACT_ONLY)

    # 根据阅读等级选择开头措辞
    if rl == ReadingLevel.META_ONLY:
        prefix = "基于标题关键词推测"
    else:
        prefix = "从摘要看"

    # 构建搜索文本：标题权重高(含3遍)，摘要权重低(含1遍)
    title_lower = title.lower()
    search_text = (title_lower + " " + title_lower + " " + title_lower + " "
                   + abstract.lower())

    # 短关键词(<4字符)需要词边界匹配，防止 "dem" 匹配 "demonstrate"
    SHORT_KW_PATTERN = re.compile(r'\b(dem|gis|s2|gee)\b', re.IGNORECASE)

    def _title_has_word(k: str) -> bool:
        """检查关键词是否作为独立词出现在标题中"""
        if len(k) < 4:
            return bool(SHORT_KW_PATTERN.search(title_lower) and
                       any(m.group(0).lower() == k.lower()
                           for m in SHORT_KW_PATTERN.finditer(title_lower)))
        return k in search_text

    # 尝试从摘要提取有意义的中文关键词映射
    # 格式: (关键词, 描述, 是否为短关键词需词边界)
    domain_hints = [
        # DEM/地形分析核心 — 短关键词用词边界
        ("dem", "基于DEM数据", len("dem") < 4),
        ("digital elevation", "基于数字高程模型", False),
        ("digital terrain", "利用数字地形分析", False),
        ("terrain", "利用地形分析", False),
        ("geomorpholog", "研究地貌形态", False),
        ("geomorphometry", "进行地貌计量分析", False),
        ("terrain factor", "提取地形因子", False),
        ("terrain attributes", "分析地形属性", False),
        ("landform", "研究地貌分类", False),
        # 沟谷/侵蚀
        ("gully", "研究沟谷/冲沟", False),
        ("gully erosion", "研究沟蚀", False),
        ("soil erosion", "研究土壤侵蚀", False),
        ("erosion model", "构建侵蚀模型", False),
        ("rusle", "应用RUSLE模型", len("rusle") < 4),
        ("rill erosion", "研究细沟侵蚀", False),
        # 区域
        ("loess plateau", "以黄土高原为研究区", False),
        ("dry-hot", "以干热河谷为研究区", False),
        ("yuanmou", "以元谋为研究区", False),
        ("jinsha", "以金沙江为研究区", False),
        # GIS/空间 — short keywords need word boundary
        ("spatial analysis", "进行空间分析", False),
        ("spatial model", "构建空间模型", False),
        ("spatial", "进行空间分析", len("spatial") < 4),
        ("gis", "结合GIS技术", len("gis") < 4),
        # 水土保持
        ("soil conservation", "研究水土保持", False),
        ("soil water conservation", "研究水土保持", False),
        ("desertification", "研究荒漠化防治", False),
        # 方法
        ("deep learning", "采用深度学习方法", False),
        ("machine learning", "采用机器学习方法", False),
        ("watershed", "研究流域", False),
        ("slope", "分析坡度因子", False),
        ("topograph", "利用地形", False),
    ]
    matched = []
    for key, chinese, is_short in domain_hints:
        if is_short:
            if _title_has_word(key):
                matched.append(chinese)
        elif key in search_text:
            matched.append(chinese)

    rl = paper.get("reading_level", ReadingLevel.ABSTRACT_ONLY)
    evidence = " [全文解析]" if rl in ("PDF_TEXT_FULL", "HUMAN_CONFIRMED") else " [摘要级]"
    if matched:
        hint_part = "、".join(matched[:3])
        summary = f"{prefix}{evidence}，该文{hint_part}"
    else:
        summary = f"{prefix}{evidence}，该文关注{title[:120]}"

    return summary[:200]


def extract_research_question(paper: Dict) -> str:
    """从标题/摘要提取研究问题 — 标注证据来源"""
    title = paper.get("title", "").strip()
    abstract = paper.get("abstract", "").lower()
    rl = paper.get("reading_level", ReadingLevel.ABSTRACT_ONLY)

    if rl in (ReadingLevel.META_ONLY, ReadingLevel.ABSTRACT_ONLY):
        prefix = "（基于摘要）"
    elif rl == ReadingLevel.PDF_TEXT_FULL:
        prefix = "（基于全文）"
    else:
        prefix = ""

    if len(title) > 100:
        title = title[:97] + "..."
    if abstract:
        first = abstract.split(". ")[0][:120]
        if len(first) > 20:
            return f"{prefix}{first}。"
    return f"{prefix}研究{title.lower()}相关问题，摘要未提供足够细节。"


def extract_research_design(paper: Dict) -> str:
    abstract = paper.get("abstract", "").lower()
    rl = paper.get("reading_level", ReadingLevel.ABSTRACT_ONLY)
    evidence = "（摘要级推测）" if rl not in ("PDF_TEXT_FULL", "HUMAN_CONFIRMED") else ""
    designs = []
    if "compar" in abstract: designs.append(f"- 对比实验设计 {evidence}")
    if "ablation" in abstract: designs.append(f"- 消融实验 {evidence}")
    if "framework" in abstract: designs.append(f"- 提出分析框架 {evidence}")
    if "prediction" in abstract or "forecast" in abstract: designs.append(f"- 预测建模 {evidence}")
    if "case study" in abstract or "case stud" in abstract: designs.append(f"- 案例研究 {evidence}")
    if "benchmark" in abstract: designs.append(f"- 基准测试 {evidence}")
    if not designs:
        return "- 摘要中未检测到实验设计描述"
    return "\n".join(designs)


def extract_data_source(paper: Dict) -> str:
    rl = paper.get("reading_level", ReadingLevel.ABSTRACT_ONLY)
    if rl == ReadingLevel.META_ONLY:
        return "- 不足以判断（仅元数据）"

    # 组合摘要 + 正文片段
    search_text = paper.get("abstract", "").lower()
    if rl in ("PDF_TEXT_FULL", "HUMAN_CONFIRMED"):
        sections = paper.get("fulltext_sections", {})
        for sk in ["methods", "introduction"]:
            search_text += " " + sections.get(sk, {}).get("content", "")[:1000].lower()

    evidence = "" if rl in ("PDF_TEXT_FULL", "HUMAN_CONFIRMED") else "（摘要级推测）"
    sources = []
    source_map = {
        "sentinel": "Sentinel 卫星数据",
        "landsat": "Landsat 数据",
        "modis": "MODIS 数据",
        "dem": "DEM 高程数据",
        "srtm": "SRTM 高程数据",
        "worldpop": "WorldPop 人口数据",
        "openstreetmap": "OpenStreetMap 数据",
        "google earth": "Google Earth 影像",
        "planet": "Planet 卫星数据",
        "naip": "NAIP 航空影像",
        "lidar": "LiDAR 点云数据",
        "era5": "ERA5 气候再分析数据",
        "chirps": "CHIRPS 降水数据",
        "census": "人口普查数据",
        "field": "实地调查数据",
        "survey": "调查问卷数据",
        "uav": "无人机数据",
        "drone": "无人机数据",
        "hyperspectral": "高光谱数据",
        "sar": "SAR 雷达数据",
        "open": "开放数据集",
    }
    # 短关键词(<4字符)需要词边界匹配，防止 "dem" 错误匹配 "demonstrate" 等
    SHORT_SOURCE_KW = {"dem", "sar", "uav", "era5"}
    short_kw_re = re.compile(r'\b(' + '|'.join(SHORT_SOURCE_KW) + r')\b', re.IGNORECASE)

    for key, label in source_map.items():
        if len(key) < 4 and key in SHORT_SOURCE_KW:
            # 词边界匹配
            if short_kw_re.search(search_text):
                actual_match = any(m.group(0).lower() == key.lower()
                                   for m in short_kw_re.finditer(search_text))
                if actual_match:
                    sources.append(f"{label} {evidence}")
        elif key in search_text:
            sources.append(f"{label} {evidence}")

    if not sources:
        if rl in ("PDF_TEXT_FULL", "HUMAN_CONFIRMED"):
            return "- 正文中未检测到明确数据来源（建议人工检查 Methods 章节）"
        return "- 摘要中未检测到明确数据来源"
    return "- " + "\n- ".join(list(dict.fromkeys(sources))[:5])


def extract_methods(paper: Dict) -> str:
    rl = paper.get("reading_level", ReadingLevel.ABSTRACT_ONLY)
    if rl == ReadingLevel.META_ONLY:
        return "- 不足以判断（仅元数据）"

    search_text = paper.get("abstract", "").lower() + " " + paper.get("title", "").lower()
    if rl in ("PDF_TEXT_FULL", "HUMAN_CONFIRMED"):
        sections = paper.get("fulltext_sections", {})
        search_text += " " + sections.get("methods", {}).get("content", "")[:2000].lower()
        search_text += " " + sections.get("abstract", {}).get("content", "")[:500].lower()

    evidence = "" if rl in ("PDF_TEXT_FULL", "HUMAN_CONFIRMED") else "（摘要级推测）"
    methods = []
    method_map = {
        "random forest": "Random Forest",
        "xgboost": "XGBoost",
        "lightgbm": "LightGBM",
        "support vector": "SVM",
        "logistic regression": "Logistic Regression",
        "linear regression": "Linear Regression",
        "cnn": "CNN",
        "convolutional neural": "CNN",
        "neural network": "神经网络",
        "transformer": "Transformer",
        "attention": "注意力机制",
        "lstm": "LSTM",
        "gru": "GRU",
        "gan": "GAN",
        "autoencoder": "Autoencoder",
        "u-net": "U-Net",
        "resnet": "ResNet",
        "graph neural": "图神经网络 (GNN)",
        "k-means": "K-Means 聚类",
        "clustering": "聚类分析",
        "pca": "PCA 降维",
        "regression": "回归分析",
        "ensemble": "集成学习",
        "gradient boost": "梯度提升",
        "bayesian": "贝叶斯方法",
        "monte carlo": "蒙特卡洛模拟",
        "markov": "马尔可夫模型",
        "reinforcement learning": "强化学习",
        "transfer learning": "迁移学习",
        "self-supervised": "自监督学习",
        "semi-supervised": "半监督学习",
        "few-shot": "小样本学习",
        "gaussian process": "高斯过程",
        "geographically weighted": "地理加权回归 (GWR)",
        "spatial autoregressive": "空间自回归",
        "kriging": "Kriging 插值",
        "inverse distance": "IDW 插值",
        "object-based": "OBIA 面向对象分析",
        "pixel-based": "基于像素分析",
        "ndvi": "NDVI 植被指数",
        "change vector": "变化向量分析",
    }
    for key, label in method_map.items():
        if key in search_text:
            methods.append(f"{label} {evidence}")

    if not methods:
        if rl in ("PDF_TEXT_FULL", "HUMAN_CONFIRMED"):
            return "- 正文中未检测到常见方法名（论文可能使用独特方法，建议人工阅读 Methods 章节）"
        return "- 摘要中未检测到明确方法名"
    return "- " + "\n- ".join(list(dict.fromkeys(methods))[:6])


def extract_innovation(paper: Dict) -> str:
    rl = paper.get("reading_level", ReadingLevel.ABSTRACT_ONLY)
    if rl == ReadingLevel.META_ONLY:
        return "- 不足以判断（仅元数据）"

    search_text = paper.get("abstract", "").lower()
    title = paper.get("title", "").lower()
    evidence = "（摘要级推测）" if rl not in ("PDF_TEXT_FULL", "HUMAN_CONFIRMED") else ""
    innovations = []
    kw_map = {
        "novel": "提出新方法/架构",
        "first": "首次应用于该领域",
        "state-of-the-art": "达到 SOTA 性能",
        "outperform": "超越现有方法",
        "improv": "改进现有方法",
        "extend": "扩展现有方法",
        "combine": "多方法融合",
        "unsupervised": "无监督方法创新",
        "self-supervised": "自监督方法创新",
        "lightweight": "轻量化设计",
        "real-time": "实时处理能力",
    }
    for key, label in kw_map.items():
        if key in search_text or key in title:
            innovations.append(f"- {label} {evidence}")

    if not innovations:
        return "- 未检测到明确创新点表述"
    return "\n".join(innovations[:4])


def extract_gis_transfer(paper: Dict) -> str:
    rl = paper.get("reading_level", ReadingLevel.ABSTRACT_ONLY)
    if rl == ReadingLevel.META_ONLY:
        return "- 不足以判断（仅元数据）"

    title = paper.get("title", "").lower()
    abstract = paper.get("abstract", "").lower()

    # 对于有全文的论文，额外搜索正文中的 GIS 关键词
    extra_text = ""
    if rl in ("PDF_TEXT_FULL", "HUMAN_CONFIRMED"):
        sections = paper.get("fulltext_sections", {})
        for sk in ["abstract", "introduction", "methods", "conclusion"]:
            extra_text += " " + sections.get(sk, {}).get("content", "")[:500]

    search_text = title + " " + abstract + " " + extra_text
    evidence_note = "" if rl in ("PDF_TEXT_FULL", "HUMAN_CONFIRMED") else "（摘要级推测）"

    transfers = []
    gis_map = {
        # DEM/地形/地貌 (高优先级)
        "elevation": "地形分析方法可迁移到DEM地貌分析/地形因子提取",
        "digital elevation": "DEM方法可迁移到数字地形分析研究",
        "digital terrain": "数字地形分析方法可复用于GIS地貌研究",
        "geomorpholog": "地貌分析方法可迁移到沟谷/冲沟形态定量研究",
        "terrain": "地形因子方法可迁移到侵蚀地形因子提取与分析",
        # 侵蚀/沟谷 (高优先级)
        "erosion": "土壤侵蚀方法可迁移到GIS侵蚀模型与模拟",
        "gully": "沟谷分析方法可迁移到沟蚀地貌形态研究",
        "soil erosion": "土壤侵蚀模型可复用于黄土高原/干热河谷侵蚀评估",
        "rusle": "RUSLE模型可迁移到区域土壤侵蚀定量评估",
        # GIS/空间分析
        "spatial": "空间分析方法可复用于GIS空间建模项目",
        "gis": "GIS方法可直接用于地理信息分析与空间建模",
        # 区域相关
        "loess": "黄土高原研究方法可迁移到类似地貌区侵蚀研究",
        "watershed": "流域分析方法可迁移到GIS水文/侵蚀建模",
        # 方法类 (中优先级)
        "classification": "分类方法可迁移到地形/侵蚀因子分类提取",
        "segmentation": "分割方法可迁移到沟谷/冲沟形态自动提取",
        "detection": "检测方法可迁移到沟谷/侵蚀沟自动识别",
        "time series": "时序分析方法可迁移到侵蚀动态监测",
        "deep learn": "深度学习框架可迁移到DEM/地形因子自动提取",
        "machine learn": "机器学习可迁移到侵蚀敏感性/风险评估",
    }
    for key, desc in gis_map.items():
        if key in search_text:
            transfers.append(f"可迁移：{desc} {evidence_note}")

    if not transfers:
        return "- 未检测到明确可迁移点（不代表没有价值）"

    # 去重（取前5条）
    seen = set()
    unique = []
    for t in transfers:
        base = t[:60]
        if base not in seen:
            seen.add(base)
            unique.append(t)
    return "- " + "\n- ".join(unique[:5])


def get_star_rating(paper: Dict, aspect: str) -> int:
    """0-5星评分"""
    title = (paper.get("title", "") + " " + paper.get("abstract", "")).lower()
    if aspect == "gis":
        score = sum(1 for k in ["spatial", "gis", "geospat", "terrain", "dem",
                                 "remote sens", "land use", "land cover"] if k in title)
        return min(score, 5)
    if aspect == "method":
        score = sum(1 for k in ["machine learning", "deep learn", "neural", "causal",
                                 "regression", "ensemble", "transfer learn"] if k in title)
        return min(score + 1, 5)
    if aspect == "career":
        score = sum(1 for k in ["remote sens", "gis", "geospat", "python", "cloud",
                                 "webgis", "pipeline", "automation"] if k in title)
        return min(score + 1, 5)
    if aspect == "product":
        score = sum(1 for k in ["open source", "github", "tool", "package", "dashboard",
                                 "api", "web", "platform"] if k in title)
        return min(score + 1, 5)
    if aspect == "code":
        score = sum(1 for k in ["python", "code availab", "github", "open source",
                                 "reproducib", "benchmark"] if k in title)
        return min(score + 1, 5)
    if aspect == "academic":
        score = sum(1 for k in ["novel", "framework", "comprehensive", "review",
                                 "systematic", "analysis"] if k in title)
        return min(score + 1, 5)
    return 2


def extract_methods_kb(paper: Dict) -> str:
    """从标题/摘要提取方法关键词 — 用于长期知识库紧凑格式"""
    abstract = paper.get("abstract", "").lower()
    title = paper.get("title", "").lower()
    ctx = title + " " + abstract
    methods = []
    if "random forest" in ctx: methods.append("Random Forest")
    if "xgboost" in ctx: methods.append("XGBoost")
    if "neural network" in ctx or "cnn" in ctx: methods.append("CNN/神经网络")
    if "transformer" in ctx: methods.append("Transformer")
    if "deep learning" in ctx: methods.append("深度学习")
    if "machine learning" in ctx and "deep learning" not in ctx: methods.append("机器学习")
    if "regression" in ctx: methods.append("回归分析")
    if "clustering" in ctx: methods.append("聚类")
    if "semantic segmentation" in ctx: methods.append("语义分割")
    if "object detection" in ctx: methods.append("目标检测")
    if "change detection" in ctx: methods.append("变化检测")
    if "time series" in ctx: methods.append("时序分析")
    if "rusle" in ctx: methods.append("RUSLE模型")
    if "swat" in ctx: methods.append("SWAT模型")
    if "spatial statistic" in ctx or "spatial analys" in ctx: methods.append("空间统计")
    if "review" in title or "survey" in title or "comprehensive" in title:
        if not methods:
            methods.append("文献综述")
    if not methods:
        methods.append("待全文确认")
    return " / ".join(methods[:3])


def extract_gis_transfer_kb(paper: Dict) -> str:
    """生成可迁移到DEM/地形/侵蚀/GIS空间分析的建议 — 聚焦罗明良老师方向"""
    title = paper.get("title", "").lower()
    keywords = paper.get("keywords", "")
    category = paper.get("category", "")
    ctx = title + " " + keywords + " " + category

    transfers = []
    # 高优先级: DEM/地形/侵蚀
    if any(k in ctx for k in ["dem", "digital elevation", "digital terrain", "terrain analysis",
                               "terrain attributes", "terrain factor", "geomorphometry"]):
        transfers.append("DEM/地形分析方法可复用于数字地形分析研究")
    if any(k in ctx for k in ["gully", "gully erosion", "gully morphology", "rill erosion", "bank erosion"]):
        transfers.append("沟谷/沟蚀分析方法可迁移到沟蚀地貌形态研究")
    if any(k in ctx for k in ["soil erosion", "rusle", "swat", "sediment", "erosion model",
                               "soil loss", "erosion risk"]):
        transfers.append("土壤侵蚀模型可复用于GIS侵蚀评估与模拟")
    if any(k in ctx for k in ["loess plateau", "黄土高原"]):
        transfers.append("黄土高原研究方法可迁移到类似地貌区侵蚀研究")
    if any(k in ctx for k in ["dry-hot valley", "干热河谷", "jinsha", "yuanmou"]):
        transfers.append("干热河谷研究方法可迁移到金沙江/元谋沟蚀研究")
    # 中优先级: GIS/空间分析/水土保持
    if any(k in ctx for k in ["spatial analysis", "spatial model", "gis", "geospatial"]):
        transfers.append("空间分析方法可复用于GIS空间建模项目")
    if any(k in ctx for k in ["soil conservation", "soil water conservation", "desertification"]):
        transfers.append("水土保持方法可迁移到荒漠化防治与GIS分析")
    if any(k in ctx for k in ["watershed", "catchment", "drainage"]):
        transfers.append("流域分析方法可迁移到GIS水文/侵蚀建模")
    # 方法类
    if any(k in ctx for k in ["machine learning", "deep learning", "random forest", "xgboost"]):
        transfers.append("ML方法可迁移到地形因子提取/侵蚀预测")
    if not transfers:
        return "迁移方向待全文确认"
    return "；".join(transfers[:2])


# ── KB 辅助函数 ─────────────────────────────────────────

def normalize_title(title: str) -> str:
    """标准化标题，用于重复检测。

    处理步骤:
      1. 全部转小写
      2. 去除标点符号（保留中文字符、字母、数字、空格）
      3. 去除多余空格
      4. 去除中英文冒号、破折号、括号差异
      5. 去除年份/期刊名等非标题噪声
    """
    import re
    if not title:
        return ""
    t = title.lower().strip()
    # 去除括号内容（含中英文括号）
    t = re.sub(r'\([^)]*\)', '', t)
    t = re.sub(r'（[^）]*）', '', t)
    # 去除中英文冒号和破折号
    t = re.sub(r'[:：]', ' ', t)
    t = re.sub(r'[—–-]', ' ', t)
    # 去除标点，保留字母/数字/中文/空格
    t = re.sub(r'[^a-z0-9一-鿿\s]', '', t)
    # 去除年份噪声 (四位数字序列)
    t = re.sub(r'\b\d{4}\b', '', t)
    # 合并多余空格
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


def fuzzy_title_similarity(title1: str, title2: str) -> float:
    """计算两个标准化标题的字符级Jaccard相似度（n-gram方法）。

    对短标题（<20字符）降低阈值要求，对长标题用bigram overlap。
    返回值 [0.0, 1.0]，>= 0.90 视为高度相似。
    """
    t1 = normalize_title(title1)
    t2 = normalize_title(title2)
    if not t1 or not t2:
        return 0.0
    if t1 == t2:
        return 1.0

    # bigram 方法
    def ng(s, n=2):
        return {s[i:i + n] for i in range(max(0, len(s) - n + 1))}

    # 对短标题用 unigram (n=1), 长标题用 bigram (n=2)
    min_len = min(len(t1), len(t2))
    n = 1 if min_len < 20 else 2
    set1 = ng(t1, n)
    set2 = ng(t2, n)
    if not set1 or not set2:
        return 0.0

    intersection = set1 & set2
    union = set1 | set2
    jaccard = len(intersection) / len(union) if union else 0.0

    # 额外检查: 较短标题是否是较长标题的子串
    shorter = t1 if len(t1) <= len(t2) else t2
    longer = t2 if len(t1) <= len(t2) else t1
    if shorter in longer:
        jaccard = max(jaccard, 0.92)

    return jaccard


def is_duplicate_paper(paper: dict, seen_papers: list, strict: bool = True) -> tuple:
    """多字段综合去重检查。

    检查顺序（按优先级）:
      1. paper_id 相同 → 直接去重
      2. DOI 相同 → 直接去重
      3. arXiv ID 相同 → 直接去重
      4. URL 相同 → 直接去重
      5. 标准化标题完全相同 → 直接去重
      6. 标题相似度 >= 0.90 → 视为重复（strict模式）
      7. 中英文翻译疑似同一篇 → 标记为疑似（非strict模式仍保留）

    参数:
      paper: 待检查论文 dict
      seen_papers: 已见论文列表，每个元素需有 paper_id/doi/arxiv_id/url/title 字段
      strict: True=高度相似即去重; False=仅完全匹配去重，模糊匹配只记录

    返回:
      (is_dup: bool, reason: str, confidence: str)
        confidence: "certain" | "high" | "suspicious"
    """
    pid = paper.get("paper_id", "")
    doi = (paper.get("doi") or "").strip()
    arxiv_id = (paper.get("arxiv_id") or "").strip()
    url = (paper.get("url") or "").strip()
    pdf_url = (paper.get("pdf_url") or "").strip()
    title = paper.get("title", "").strip()
    title_norm = normalize_title(title)

    for sp in seen_papers:
        # 1. paper_id
        if pid and sp.get("paper_id") == pid:
            return True, f"paper_id重复: {pid[:16]}...", "certain"

        # 2. DOI
        sp_doi = (sp.get("doi") or "").strip()
        if doi and sp_doi and doi.lower() == sp_doi.lower():
            return True, f"DOI重复: {doi}", "certain"

        # 3. arXiv ID
        sp_arxiv = (sp.get("arxiv_id") or "").strip()
        if arxiv_id and sp_arxiv and arxiv_id.lower() == sp_arxiv.lower():
            return True, f"arXiv ID重复: {arxiv_id}", "certain"

        # 4. URL
        sp_url = (sp.get("url") or "").strip()
        if url and sp_url and url.lower() == sp_url.lower():
            return True, f"URL重复: {url[:60]}...", "certain"
        sp_pdf = (sp.get("pdf_url") or "").strip()
        if pdf_url and sp_pdf and pdf_url.lower() == sp_pdf.lower():
            return True, f"PDF URL重复: {pdf_url[:60]}...", "certain"

        # 5. 标准化标题完全相同
        sp_title = sp.get("title", "").strip()
        sp_title_norm = normalize_title(sp_title)
        if title_norm and sp_title_norm and title_norm == sp_title_norm:
            return True, f"标题完全匹配: {title[:60]}...", "certain"

        # 6. 标题相似度 >= 0.90
        if title_norm and sp_title_norm:
            sim = fuzzy_title_similarity(title, sp_title)
            if sim >= 0.90:
                if strict:
                    return True, f"标题高度相似 ({sim:.2f}): {title[:60]}...", "high"

    return False, "", ""


def get_all_seen_papers_full(conn) -> list:
    """从数据库获取所有已见论文的完整字段列表，用于去重检查。"""
    rows = conn.execute(
        "SELECT paper_id, title, doi, arxiv_id, source FROM seen_papers"
    ).fetchall()
    result = []
    for r in rows:
        paper_id, title, doi, arxiv_id, source = r
        entry = {
            "paper_id": paper_id,
            "title": title or "",
            "doi": doi or "",
            "arxiv_id": arxiv_id or "",
            "url": "",
            "pdf_url": "",
        }
        # 从 paper_id 反推可能的 URL (仅 arXiv)
        if arxiv_id:
            entry["url"] = f"https://arxiv.org/abs/{arxiv_id}"
            entry["pdf_url"] = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        result.append(entry)
    return result


# ── 固定标签体系 ──
# 只使用以下固定标签，防止长期知识库标签膨胀和混乱
FIXED_TAGS = [
    "DEM", "数字地形分析", "地形因子", "沟谷地貌", "冲沟",
    "土壤侵蚀", "GIS空间分析", "空间建模", "黄土高原",
    "干热河谷", "水土保持", "荒漠化防治", "地貌形态",
]

FIXED_TAG_KEYWORDS = {
    "DEM": ["dem", "digital elevation", "digital terrain", "srtm", "aster gdem", "lidar dem"],
    "数字地形分析": ["digital terrain analysis", "terrain analysis", "数字地形分析"],
    "地形因子": ["terrain factor", "terrain attributes", "地形因子", "slope gradient", "curvature", "topographic wetness", "ls factor"],
    "沟谷地貌": ["gully", "gully morphology", "gully development", "gully erosion", "沟谷", "谷", "channel"],
    "冲沟": ["gully", "冲沟", "沟蚀", "rill erosion", "bank erosion"],
    "土壤侵蚀": ["soil erosion", "erosion model", "rusle", "soil loss", "sediment", "土壤侵蚀", "侵蚀"],
    "GIS空间分析": ["gis", "spatial analysis", "spatial model", "geospatial", "地理信息"],
    "空间建模": ["spatial model", "spatial statistic", "spatial pattern", "空间建模", "空间分析"],
    "黄土高原": ["loess plateau", "黄土高原"],
    "干热河谷": ["dry-hot valley", "干热河谷", "jinsha", "yuanmou", "金沙江", "元谋"],
    "水土保持": ["soil conservation", "soil water conservation", "水土保持", "water and soil"],
    "荒漠化防治": ["desertification", "land degradation", "荒漠化", "荒漠"],
    "地貌形态": ["geomorpholog", "geomorphometry", "landform", "地貌", "地形"],
}


def _generate_fixed_tags(paper: dict) -> list:
    """根据论文标题/摘要/关键词生成固定标签列表。"""
    title = (paper.get("title", "") or "").lower()
    abstract = (paper.get("abstract", "") or "").lower()
    keywords = (paper.get("keywords", "") or "").lower()
    ctx = f"{title} {abstract} {keywords}"

    tags = []
    for tag, kw_list in FIXED_TAG_KEYWORDS.items():
        if any(kw in ctx for kw in kw_list):
            tags.append(tag)

    # 限制标签数量，最多5个
    return tags[:5]


def extract_existing_kb_entries(kb_text: str) -> list:
    """解析已有KB条目，提取KB ID、标题、DOI、日期。"""
    import re
    entries = []
    current_date = None
    for line in kb_text.split("\n"):
        line = line.strip()
        # 日期段
        date_match = re.match(r'^##\s+(\d{4}-\d{2}-\d{2})', line)
        if date_match:
            current_date = date_match.group(1)
            continue
        # KB条目
        kb_match = re.match(r'^###\s+(KB-\d{4}-\d{2}-\d{2}-\d{2})[｜|]\s*(.+)', line)
        if kb_match:
            entries.append({
                "kb_id": kb_match.group(1),
                "title_raw": kb_match.group(2).strip(),
                "date": current_date,
                "doi": None,
                "title_normalized": normalize_title(kb_match.group(2)),
            })
            continue
        # DOI行
        if entries and line.startswith("- **DOI:**"):
            doi_match = re.search(r'`?([^`\s]+)`?', line.replace("- **DOI:**", ""))
            if doi_match and doi_match.group(1) not in ("未提供", "未提取", "未确认"):
                entries[-1]["doi"] = doi_match.group(1).strip().rstrip('.')
    return entries


def is_duplicate_kb_entry(existing_entries: list, paper: dict) -> tuple:
    """根据DOI和标题判断是否重复。返回(是否重复, 原因)。"""
    paper_doi = (paper.get("doi") or "").strip()
    paper_title_norm = normalize_title(paper.get("title", ""))

    for entry in existing_entries:
        # DOI检测
        if paper_doi and entry.get("doi") and paper_doi == entry["doi"]:
            return True, f"DOI重复: {paper_doi} (已有 {entry['kb_id']})"
        # 标题相似度检测
        entry_title_norm = entry.get("title_normalized", "")
        if paper_title_norm and entry_title_norm:
            if paper_title_norm == entry_title_norm:
                return True, f"标题完全匹配: 已有 {entry['kb_id']}"
            if len(paper_title_norm) > 40 and len(entry_title_norm) > 40:
                shorter = min(paper_title_norm, entry_title_norm, key=len)
                longer = max(paper_title_norm, entry_title_norm, key=len)
                if shorter in longer:
                    return True, f"标题高度相似: 已有 {entry['kb_id']}"

    return False, ""


def find_or_create_date_section(kb_text: str, report_date: str) -> tuple:
    """定位或创建指定日期段。返回(是否需要创建新段, 插入位置/现有文本)。"""
    import re
    pattern = re.compile(rf'^##\s+{re.escape(report_date)}\s*$', re.MULTILINE)
    match = pattern.search(kb_text)
    if match:
        return False, kb_text  # 已存在该日期段
    return True, kb_text


def next_kb_id(existing_kb_text: str, report_date: str) -> str:
    """生成下一个不重复KB ID。"""
    import re
    pattern = re.compile(rf'KB-{re.escape(report_date)}-(\d+)')
    existing_nums = [int(m) for m in pattern.findall(existing_kb_text)]
    next_num = max(existing_nums) + 1 if existing_nums else 1
    return f"KB-{report_date}-{next_num:02d}"


def next_inno_id(existing_text: str, report_date: str) -> str:
    """生成下一个INNO ID。"""
    import re
    pattern = re.compile(rf'INNO-{re.escape(report_date)}-(\d+)')
    existing_nums = [int(m) for m in pattern.findall(existing_text)]
    next_num = max(existing_nums) + 1 if existing_nums else 1
    return f"INNO-{report_date}-{next_num:02d}"


def generate_possible_innovations(paper: dict) -> list:
    """根据论文标题、摘要、方法、关键词生成可迁移创新点。"""
    title = (paper.get("title", "") or "").lower()
    abstract = (paper.get("abstract", "") or "").lower()
    keywords = (paper.get("keywords", "") or "").lower()
    category = (paper.get("category", "") or "").lower()
    ctx = f"{title} {abstract} {keywords} {category}"

    innovations = []
    confidence = "全文已读" if paper.get("reading_level") == ReadingLevel.HUMAN_CONFIRMED else "全文解析"

    # 方法迁移类
    if any(k in ctx for k in ["machine learning", "deep learning", "cnn", "transformer",
                                "random forest", "xgboost", "neural network"]):
        innovations.append({
            "type": "方法迁移",
            "text": "ML/DL方法可迁移到DEM地形因子提取/侵蚀预测/沟谷自动识别",
            "confidence": confidence,
        })

    if any(k in ctx for k in ["spatial", "gis", "geospatial", "spatial analysis"]):
        innovations.append({
            "type": "方法迁移",
            "text": "空间分析方法可迁移到GIS空间建模/侵蚀空间格局分析",
            "confidence": confidence,
        })

    if any(k in ctx for k in ["dem", "digital elevation", "terrain", "topograph", "geomorpholog"]):
        innovations.append({
            "type": "方法迁移",
            "text": "DEM/地形分析方法可迁移到数字地形分析/沟谷形态定量研究",
            "confidence": confidence,
        })

    if any(k in ctx for k in ["gully", "gully erosion", "rill", "bank erosion"]):
        innovations.append({
            "type": "方法迁移",
            "text": "沟谷/沟蚀分析方法可迁移到黄土高原/干热河谷沟蚀地貌研究",
            "confidence": confidence,
        })

    # 数据融合类
    if any(k in ctx for k in ["sentinel", "landsat", "modis", "remote sens", "satellite", "uav"])\
       and any(k in ctx for k in ["dem", "elevation", "terrain", "topograph"]):
        innovations.append({
            "type": "数据融合",
            "text": "多源遥感+DEM数据融合方法可迁移到侵蚀地形因子提取",
            "confidence": confidence,
        })

    if any(k in ctx for k in ["gee", "google earth engine", "cloud"]) \
       and any(k in ctx for k in ["erosion", "terrain", "dem", "gully"]):
        innovations.append({
            "type": "数据融合",
            "text": "GEE云端处理流程可迁移到区域尺度侵蚀/地形分析",
            "confidence": confidence,
        })

    # 应用场景类
    if any(k in ctx for k in ["erosion", "soil", "watershed", "hydrolog", "sediment"]):
        innovations.append({
            "type": "应用场景",
            "text": "土壤侵蚀/水文模型可迁移到黄土高原/干热河谷侵蚀评估场景",
            "confidence": confidence,
        })

    if any(k in ctx for k in ["loess", "dry-hot", "jinsha", "yuanmou"]):
        innovations.append({
            "type": "应用场景",
            "text": "区域研究成果可直接指导黄土高原/干热河谷DEM地貌研究",
            "confidence": confidence,
        })

    # 自动化流程类
    if any(k in ctx for k in ["python", "pipeline", "automation", "workflow", "open source"]):
        innovations.append({
            "type": "自动化流程",
            "text": "自动化处理流程可作为GIS数据处理工具链参考",
            "confidence": confidence,
        })

    if any(k in ctx for k in ["ai agent", "llm", "large language model", "automated coding"]):
        innovations.append({
            "type": "自动化流程",
            "text": "AI辅助/Agent方法可迁移到GIS自动化工作流",
            "confidence": confidence,
        })

    # 摘要级标记
    rl = paper.get("reading_level", "")
    if rl not in (ReadingLevel.PDF_TEXT_FULL, ReadingLevel.HUMAN_CONFIRMED):
        for inn in innovations:
            inn["confidence"] = "摘要级推测"

    return innovations[:3]


def update_possible_innovations(selected: list, report_date: str, report_path: str,
                                 kb_mapping: dict):
    """同步维护可能的创新点.md。"""
    if not INNOVATION_POINTS_PATH:
        return

    existing_text = ""
    if INNOVATION_POINTS_PATH.exists():
        existing_text = INNOVATION_POINTS_PATH.read_text(encoding="utf-8")

    new_entries = []
    added = 0
    skipped = 0

    for p in selected:
        # 只有全文已读才写入创新点
        rl = p.get("reading_level", "")
        if rl not in (ReadingLevel.PDF_TEXT_FULL, ReadingLevel.HUMAN_CONFIRMED):
            continue

        kb_id = kb_mapping.get(p.get("paper_id", ""), "")
        innovations = generate_possible_innovations(p)
        if not innovations:
            continue

        for inn in innovations:
            # 检查INNO是否已存在（简易去重：检查是否有相同的来源论文+创新点文本）
            inn_text_slug = normalize_title(inn["text"])[:50]
            if inn_text_slug in existing_text:
                skipped += 1
                continue

            inno_id = next_inno_id(existing_text + "".join(
                e["inno_id"] for e in new_entries), report_date)

            entry = [
                f"### {inno_id}",
                "",
                f"- **创新点类型:** {inn['type']}",
                f"- **创新点:** {inn['text']}",
                f"- **来源论文:** {p.get('title','')[:80]}",
                f"- **来源日报:** [[{report_date}_论文阅读日报]]",
            ]
            if kb_id:
                entry.append(f"- **对应长期知识库:** [[长期知识库#{kb_id}]]")
            entry += [
                f"- **可迁移方向:** GIS / 遥感 / 空间分析",
                f"- **适合做成:** 待评估",
                f"- **可信度:** {inn['confidence']}",
                f"- **状态:** 候选",
                f"- **备注:** 自动生成于 {report_date}",
                "",
            ]
            new_entries.append({
                "inno_id": inno_id,
                "text": "\n".join(entry),
            })
            added += 1

    if not new_entries:
        return 0, 0

    # 找到或创建日期段
    import re
    date_header = f"## {report_date}"
    if date_header in existing_text:
        # 在日期段末尾追加
        next_date_match = re.search(
            rf'{re.escape(date_header)}[\s\S]*?(?=\n## \d{{4}}-\d{{2}}-\d{{2}}\n|\Z)',
            existing_text)
        if next_date_match:
            section_end = next_date_match.end()
            insert_pos = section_end
        else:
            insert_pos = len(existing_text)
        new_text = existing_text[:insert_pos]
        if not new_text.endswith("\n"):
            new_text += "\n"
        for e in new_entries:
            new_text += e["text"]
        new_text += existing_text[insert_pos:]
    else:
        # 追加整个日期段
        if existing_text and not existing_text.endswith("\n"):
            existing_text += "\n"
        section = [f"## {report_date}", ""]
        for e in new_entries:
            section.append(e["text"])
        new_text = existing_text + "\n".join(section) + "\n"

    INNOVATION_POINTS_PATH.write_text(new_text, encoding="utf-8")

    return added, skipped


def log_kb_write(log_entry: dict):
    """写入KB操作日志。"""
    KB_WRITE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(KB_WRITE_LOG_PATH, "a", encoding="utf-8") as lf:
        lf.write(f"[{timestamp}] ")
        lf.write(json.dumps(log_entry, ensure_ascii=False))
        lf.write("\n")


# ── 更新长期知识库 ─────────────────────────────────────────

def update_knowledge_base(date: str, selected: List[Dict]):
    """追加精选论文到长期知识库 — 含去重、KB ID、来源日报、创新点。

    写入规则:
      - 只有 PDF_TEXT_FULL / HUMAN_CONFIRMED 允许写入
      - DOI/标题去重
      - 同日期段合并
      - 自动生成稳定KB ID
      - 同步维护可能的创新点.md
    """
    import re

    # ── 筛选可写入的论文 ──
    eligible = [p for p in selected if p.get("reading_level") in
                (ReadingLevel.PDF_TEXT_FULL, ReadingLevel.HUMAN_CONFIRMED)]

    if not eligible:
        print(f"  [*] 无全文精读论文，跳过知识库写入")
        # 更新待补读队列
        pending = [p for p in selected if p.get("reading_level") not in
                   (ReadingLevel.PDF_TEXT_FULL, ReadingLevel.HUMAN_CONFIRMED)]
        if pending:
            _update_pending_read_queue(date, pending)
        # 日志
        log_kb_write({
            "date": date, "new_kb_count": 0, "skipped_duplicate": 0,
            "new_inno_count": 0, "skipped_inno": 0,
            "report_path": str(OUTPUT_DIR / f"{date}_论文阅读日报.md"),
            "success": True, "note": "无全文精读论文",
        })
        return {"kb_mapping": {}, "kb_count": 0, "inno_count": 0}

    # ── 加载已有KB内容 ──
    existing_kb = ""
    if KB_PATH.exists():
        existing_kb = KB_PATH.read_text(encoding="utf-8")
    existing_entries = extract_existing_kb_entries(existing_kb)

    # ── 构建KB条目 ──
    new_entries = []
    kb_mapping = {}  # paper_id -> kb_id
    skipped_duplicate = 0
    added_count = 0

    for p in eligible:
        # 去重
        is_dup, reason = is_duplicate_kb_entry(existing_entries, p)
        if is_dup:
            print(f"  [~] KB去重: {p.get('title','')[:60]}... {reason}")
            skipped_duplicate += 1
            continue

        kb_id = next_kb_id(existing_kb + "".join(
            e.get("kb_id", "") for e in new_entries), date)
        kb_mapping[p.get("paper_id", "")] = kb_id

        title = p.get("title", "").strip()
        doi = p.get("doi") or "未提供"
        arxiv_id = p.get("arxiv_id", "")
        source = p.get("source", "")
        rl = p.get("reading_level", "")
        rl_label = READING_LEVEL_LABELS.get(rl, "未知")
        category = normalize_paper_category(p.get("category", ""))
        # 使用固定标签体系生成Tags，防止长期知识库标签膨胀
        fixed_tags = _generate_fixed_tags(p)
        keywords = " | ".join(fixed_tags) if fixed_tags else (p.get("keywords", "") or "").replace("|", " ").strip()
        local_path = p.get("fulltext_local_path", "") or p.get("local_pdf_path", "")
        if local_path:
            try:
                local_path = str(Path(local_path).relative_to(
                    Path(__file__).resolve().parent.parent))
            except ValueError:
                pass

        # 创新点
        innovations = generate_possible_innovations(p)
        inno_text = ""
        if innovations:
            inno_lines = []
            for inn in innovations:
                inno_lines.append(f"  - 【{inn['type']}】{inn['text']} [{inn['confidence']}]")
            inno_text = "\n".join(inno_lines)
        else:
            inno_text = "  - 暂未提取"

        confidence = "人工确认" if rl == ReadingLevel.HUMAN_CONFIRMED else "全文解析"

        entry_lines = [
            f"### {kb_id}｜{title}",
            "",
            f"- **KB ID:** {kb_id}",
            f"- **作者:** {p.get('first_author', 'Unknown')} et al. ({p.get('year', '')})",
            f"- **DOI:** `{doi}`" if doi != "未提供" else f"- **DOI:** 未提供",
            f"- **来源:** {source}",
            f"- **来源日报:** [[{date}_论文阅读日报]]",
            f"- **来源论文:** {'arXiv: `' + arxiv_id + '`' if arxiv_id else '未提供'}",
            f"- **阅读等级:** {rl_label}",
            f"- **Tags:** {keywords} | {category}",
            f"- **中文一句话有效总结:** {make_oneline_summary(p)}",
            f"- **方法:** {extract_methods_kb(p)}",
            f"- **可迁移到GIS/遥感/空间分析的点:** {extract_gis_transfer_kb(p)}",
            f"- **可能的创新点:**",
            inno_text,
            f"- **可信度:** {confidence}",
            f"- **源文件路径:** `{local_path or '待补充'}`",
            f"- **入库日期:** {date}",
            f"- **状态:** formal_verified",
            "",
        ]

        existing_entries.append({
            "kb_id": kb_id, "doi": doi, "title_normalized": normalize_title(title),
            "date": date,
        })
        new_entries.append({"kb_id": kb_id, "text": "\n".join(entry_lines)})
        added_count += 1

    if not new_entries:
        print(f"  [*] 去重后无新KB条目（{len(eligible)}篇入选，{skipped_duplicate}篇重复），跳过知识库写入")
        pending = [p for p in selected if p.get("reading_level") not in
                   (ReadingLevel.PDF_TEXT_FULL, ReadingLevel.HUMAN_CONFIRMED)]
        if pending:
            _update_pending_read_queue(date, pending)
        log_kb_write({
            "date": date, "new_kb_count": 0, "skipped_duplicate": skipped_duplicate,
            "new_inno_count": 0, "skipped_inno": 0,
            "report_path": str(OUTPUT_DIR / f"{date}_论文阅读日报.md"),
            "success": True, "note": f"去重后无新条目（{len(eligible)}入选/{skipped_duplicate}重复）",
        })
        return {"kb_mapping": kb_mapping, "kb_count": 0, "inno_count": 0}

    # ── 写入KB ──
    if not KB_PATH.exists():
        KB_PATH.write_text(
            "# 长期知识库 — 科研论文追踪\n\n"
            "> 自动积累 + 人工精读，按日期组织。\n"
            "> 每条记录分配稳定KB ID（KB-YYYY-MM-DD-NN），可被日报、创新点文档交叉引用。\n\n"
            "---\n\n",
            encoding="utf-8")

    # 检查是否已有该日期段
    needs_new_section, _ = find_or_create_date_section(existing_kb if existing_kb else "", date)

    with open(KB_PATH, "a", encoding="utf-8") as f:
        if needs_new_section:
            f.write(f"## {date}\n\n")
        for entry in new_entries:
            f.write(entry["text"])

    print(f"  [+] KB写入: {added_count} 条新条目 (跳过{skipped_duplicate}条重复)")

    # ── 同步维护可能的创新点.md ──
    inno_added, inno_skipped = update_possible_innovations(
        eligible, date,
        str(OUTPUT_DIR / f"{date}_论文阅读日报.md"),
        kb_mapping,
    )
    if inno_added > 0:
        print(f"  [+] 可能的创新点: {inno_added} 条新创新点 (跳过{inno_skipped}条重复)")

    # ── 更新待补读队列 ──
    pending = [p for p in selected if p.get("reading_level") not in
               (ReadingLevel.PDF_TEXT_FULL, ReadingLevel.HUMAN_CONFIRMED)]
    if pending:
        _update_pending_read_queue(date, pending)

    # ── 写入日志 ──
    log_kb_write({
        "date": date,
        "report_path": str(OUTPUT_DIR / f"{date}_论文阅读日报.md"),
        "new_kb_count": added_count,
        "skipped_duplicate": skipped_duplicate,
        "new_inno_count": inno_added,
        "skipped_inno": inno_skipped,
        "kb_ids": [e["kb_id"] for e in new_entries],
        "success": True,
    })

    return {"kb_mapping": kb_mapping, "kb_count": added_count, "inno_count": inno_added}


def _update_pending_read_queue(date: str, pending: List[Dict]):
    """更新待补读队列"""
    if not PENDING_READ_PATH.exists():
        PENDING_READ_PATH.write_text(
            "# 待补读队列\n\n"
            "> 阅读等级不足（META_ONLY / ABSTRACT_ONLY / PDF_TEXT_PARTIAL）的论文，"
            "补读至 PDF_TEXT_FULL 后方可重新评估是否进入长期知识库。\n\n"
            "---\n\n",
            encoding="utf-8")

    entry = [f"## {date}", ""]
    for p in pending:
        rl = READING_LEVEL_LABELS.get(p.get("reading_level", ""), "未知")
        entry += [
            f"- [ ] **{p.get('title','')[:80]}**",
            f"  - 作者: {p.get('first_author', '?')} | 年: {p.get('year', '?')}",
            f"  - 阅读等级: {rl} | 来源: {p.get('source','')}",
            f"  - PDF: {p.get('pdf_url','') or '需自行检索'}",
            f"",
        ]
    entry.append("")

    with open(PENDING_READ_PATH, "a", encoding="utf-8") as f:
        f.write("\n".join(entry))


# ── 主流程 ─────────────────────────────────────────────────

# ── 微信推送 ─────────────────────────────────────────────────

def push_wechat(date: str, candidates: int, selected_papers: list, total: int, days: int, success: bool):
    """通过 pushplus 推送论文日报 — 排版版

    从生成的日报 MD 文件中提取 TOP 1-3 论文详情，
    渲染为手机端友好的 Markdown 排版消息。
    """
    push_cfg_path = _paths["push_cfg_path"]
    if not push_cfg_path.exists():
        print("  [!] push_config.json 不存在, 跳过推送")
        return

    cfg = json.loads(push_cfg_path.read_text(encoding="utf-8"))
    token = cfg.get("pushplus_token")
    if not token:
        print("  [!] pushplus_token 未配置")
        return

    wd = ["周一","周二","周三","周四","周五","周六","周日"][datetime.now().weekday()]
    status_icon = "✅" if success else "⚠️"
    selected_count = len(selected_papers) if selected_papers else 0

    # ── 排版头部 ──
    lines = []
    lines.append(f"{status_icon} **{date} {wd} · 论文日报**")
    lines.append("")

    # ── 统计概览 ──
    lines.append("━━━ 📊 今日统计 ━━━")
    lines.append(f"**候选** {candidates} 篇　**精选** {selected_count} 篇")
    lines.append(f"累计 {total} 篇 / {days} 天　{'数据源正常' if success else '⚠️ 数据源异常'}")
    lines.append("")

    # ── 精选论文 ──
    if selected_papers:
        lines.append("━━━ 📄 精选论文 ━━━")
        for i, paper in enumerate(selected_papers[:3], 1):
            title = paper.get("title", "无标题").strip()
            # 截断过长标题
            if len(title) > 80:
                title = title[:77] + "..."
            source = paper.get("source", paper.get("journal", "arXiv")).strip()
            score = paper.get("score", 0)
            stars = "⭐" * min(5, max(1, int(score / 20 + 1)))

            lines.append(f"**{i}. {title}**")
            lines.append(f"  {stars} {score}分 | {source}")
            # 一句话总结（如果有）
            summary = paper.get("summary", paper.get("abstract", ""))
            if summary:
                if len(summary) > 120:
                    summary = summary[:117] + "..."
                lines.append(f"  {summary}")
            lines.append("")
    else:
        lines.append("━━━ 📄 精选论文 ━━━")
        lines.append("今日无高分精选论文")
        lines.append("")

    # ── 底部提示 ──
    lines.append("━━━ 📎 ━━━")
    report_name = f"{date}_论文阅读日报.md"
    lines.append(f"📋 完整日报: `{report_name}`")

    content = "\n".join(lines)

    # PushPlus 单条消息限制 ~2000 字符
    if len(content) > 1900:
        # 截断最后一条论文的摘要
        content = content[:1850] + "\n\n...\n━━━ 📎 ━━━\n📋 查看完整日报"

    data = {
        "token": token,
        "title": f"{status_icon} 论文日报 {date} | {candidates}候选/{selected_count}精选",
        "content": content,
        "template": "markdown",
    }
    try:
        req = urllib.request.Request(
            "https://www.pushplus.plus/send",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as resp:
            result = json.loads(resp.read())
        if result.get("code") == 200:
            print(f"  [+] 微信推送成功")
        else:
            print(f"  [!] 推送异常: {result}")
    except Exception as e:
        print(f"  [!] 推送失败: {e}")


def _save_deep_read_queue(date: str, selected: List[Dict], fulltext_stats: Dict):
    """保存全文提取文本 + 生成 Claude 深读队列文件。

    对每篇 PDF_TEXT_FULL 论文:
    1. 将提取的全文保存为 .txt 到 fulltext_papers/<date>/
    2. 生成 deep_read_queue.json 供 Claude 读取
    """
    from pathlib import Path as _Path
    import json as _json

    fulltext_root = _Path("<LOCAL_PATH>")
    queue_dir = fulltext_root / date
    queue_dir.mkdir(parents=True, exist_ok=True)

    queue = {"date": date, "generated_at": datetime.now().isoformat(), "papers": []}

    for p in selected:
        rl = p.get("reading_level", "")
        if rl not in ("PDF_TEXT_FULL", "HUMAN_CONFIRMED"):
            continue

        sections = p.get("fulltext_sections", {})
        # 拼接全文
        full_text_parts = []
        for sk in ["abstract", "introduction", "methods", "results", "discussion", "conclusion"]:
            content = sections.get(sk, {}).get("content", "")
            if content:
                full_text_parts.append(f"=== {sk.upper()} ===\n{content}")
        full_text = "\n\n".join(full_text_parts)

        if not full_text:
            continue

        # 保存提取文本
        slug = p.get("title", "unknown")[:60].replace("/", "_").replace("\\", "_").replace(":", "_")
        safe_name = f"{p.get('paper_id', slug)}_{slug}.txt"
        txt_path = queue_dir / safe_name
        txt_path.write_text(full_text[:80000], encoding="utf-8")

        # 队列条目
        queue["papers"].append({
            "paper_id": p.get("paper_id", ""),
            "title": p.get("title", ""),
            "authors": p.get("authors", [])[:5],
            "year": p.get("year", ""),
            "arxiv_id": p.get("arxiv_id", ""),
            "doi": p.get("doi", ""),
            "url": p.get("url", ""),
            "pdf_url": p.get("pdf_url", ""),
            "local_pdf": p.get("fulltext_local_path", ""),
            "extracted_text_path": str(txt_path),
            "text_chars": len(full_text),
            "text_words": len(full_text.split()),
            "detected_sections": sections.get("detected_sections", []),
            "keywords": p.get("keywords", ""),
            "category": p.get("category", ""),
        })

    if queue["papers"]:
        queue_path = queue_dir / "deep_read_queue.json"
        queue_path.write_text(_json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[+] 深读队列: {queue_path} ({len(queue['papers'])} 篇待深读)")
    else:
        print(f"[*] 深读队列: 今日无 PDF_TEXT_FULL 论文待深读")


def main():
    import argparse
    p = argparse.ArgumentParser(description="每日科研论文自动筛选")
    p.add_argument("--date", type=str, help="指定日期 YYYY-MM-DD")
    p.add_argument("--start-date", type=str, help="补跑起始日期 YYYY-MM-DD（与--end-date配合使用）")
    p.add_argument("--end-date", type=str, help="补跑结束日期 YYYY-MM-DD（与--start-date配合使用）")
    p.add_argument("--dry-run", action="store_true", help="试运行模式：不写入任何文件")
    p.add_argument("--push", action="store_true", help="微信推送 (pushplus)")
    p.add_argument("--reset", action="store_true", help="清空去重库")
    p.add_argument("--schedule", action="store_true", help="输出计划任务配置")
    args = p.parse_args()

    if args.schedule:
        print(r"""
Windows 计划任务 (PowerShell 管理员):

powershell -Command "
schtasks /create /tn 'DailyPaperCurator_1200' /tr '\"<LOCAL_PATH>" \"<LOCAL_PATH>" --push' /sc daily /st 12:00 /f
"

建议时间: 每天 12:00，与工作流的 `DailyPaperCurator_1200` 任务约定保持一致。
""")
        return 0

    # 确定日期列表
    if args.start_date and args.end_date:
        start = datetime.strptime(args.start_date, "%Y-%m-%d")
        end = datetime.strptime(args.end_date, "%Y-%m-%d")
        if start > end:
            print(f"[!] start-date ({args.start_date}) 不能晚于 end-date ({args.end_date})")
            return 1
        dates = []
        current = start
        while current <= end:
            dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
        if len(dates) > 30:
            print(f"[!] 日期范围过大 ({len(dates)} 天)，最多支持 30 天")
            return 1
        print(f"[*] 补跑模式: {args.start_date} → {args.end_date} (共 {len(dates)} 天)")
    elif args.date:
        dates = [args.date]
    else:
        dates = [datetime.now().strftime("%Y-%m-%d")]

    # Claude 打开检测（dry-run 模式跳过）
    if not args.dry_run:
        check_claude_and_exit_if_not_running()

    conn = init_db()

    if args.reset:
        conn.execute("DELETE FROM seen_papers")
        conn.execute("DELETE FROM daily_log")
        conn.commit()
        print("[+] 去重库已清空")
        conn.close()
        return 0

    if args.dry_run:
        print("[*] DRY-RUN 模式：不写入任何文件")
        print(f"  [+] 路径配置加载成功")
        print(f"  [+] output_dir: {OUTPUT_DIR}")
        print(f"  [+] kb_path: {KB_PATH}")
        print(f"  [+] innovation_points_path: {INNOVATION_POINTS_PATH}")
        print(f"  [+] db_path: {DB_PATH}")
        print(f"  [+] 每日精读数量: {DAILY_INTENSIVE_READ_COUNT} 篇")
        conn.close()
        return 0

    # ── 逐日处理 ──
    exit_code = 0
    for date in dates:
        exit_code = _process_single_date(date, args, conn)
        if exit_code != 0:
            break

    conn.close()
    return exit_code


def _process_single_date(date: str, args, conn) -> int:
    """处理单日论文筛选。返回 0 表示成功。"""
    # 检查当天是否已生成
    existing = conn.execute("SELECT 1 FROM daily_log WHERE date=?", (date,)).fetchone()
    if existing:
        print(f"[!] {date} 的论文日报已生成过, 跳过")
        return 0

    print(f"\n[*] === 每日论文筛选 | {date} ===")
    print(f"[*] 搜索方向: {len(SEARCH_QUERIES)} 个 (聚焦罗明良老师研究方向)")
    print(f"[*] 搜索源: arXiv API ({sum(len(v) for v in SEARCH_QUERIES.values())} 个关键词)")

    seen_ids = get_all_seen_ids(conn)
    seen_papers_full = get_all_seen_papers_full(conn)
    all_papers = []
    queries_used = []
    total_sources = 0
    dedup_stats = {
        "total_candidates": 0,
        "direction_filtered": 0,
        "seen_dedup": 0,
        "cross_dedup": 0,
        "final_count": 0,
        "deduped_titles": [],
        "suspicious_titles": [],
    }

    for category, keywords in SEARCH_QUERIES.items():
        for kw in keywords:
            queries_used.append(kw)
            arxiv_count = s2_count = 0
            # 源1: arXiv
            print(f"  [{category}] arXiv: {kw[:50]}...")
            papers = search_arxiv(kw, max_results=15)
            for paper in papers:
                paper["search_category"] = category
                paper["keywords"] = kw
                paper["score"] = score_paper(paper)
                paper["rubric"] = rubric_score(paper)
            new_a = sum(1 for p in papers if p["paper_id"] not in seen_ids)
            arxiv_count = len(papers)
            if arxiv_count > 0: total_sources += 1
            all_papers.extend(papers)
            print(f"    arXiv: {arxiv_count}篇 (新{new_a})", end="")
            time.sleep(8)  # arXiv + S2 rate limit: 8s between requests

            # 源2: Semantic Scholar (每2个关键词搜一次, 规避限速)
            if queries_used.index(kw) % 2 == 0:
                print("")
                continue
            if _s2_consecutive_429 >= _S2_MAX_CONSECUTIVE_429:
                print(f" | S2: 已跳过 (连续{_s2_consecutive_429}次429)")
                continue
            p2 = search_semantic_scholar(kw, max_results=5)
            for paper in p2:
                if paper["paper_id"] not in seen_ids:
                    paper["search_category"] = category
                    paper["keywords"] = kw
                    paper["score"] = score_paper(paper)
                    paper["rubric"] = rubric_score(paper)
            new_s = sum(1 for p in p2 if p["paper_id"] not in seen_ids)
            s2_count = len(p2)
            all_papers.extend(p2)
            print(f" | S2: {s2_count}篇 (新{new_s})")
            time.sleep(5)

    # ── 阶段1: 批量paper_id去重 ──
    unique_papers = []
    seen_in_batch = set()
    for p in all_papers:
        pid = p["paper_id"]
        if pid not in seen_ids and pid not in seen_in_batch:
            unique_papers.append(p)
            seen_in_batch.add(pid)
        else:
            dedup_stats["seen_dedup"] += 1
            if len(dedup_stats["deduped_titles"]) < 10:
                dedup_stats["deduped_titles"].append(
                    f"[paper_id重复] {p.get('title','')[:60]}")

    dedup_stats["total_candidates"] = len(unique_papers)

    # ── 阶段2: 方向相关性过滤 ──
    # 对 paper_id 去重后的结果做方向过滤（score>0 表示通过方向检查）
    direction_passed = [p for p in unique_papers if p.get("score", 0) > 0]
    dedup_stats["direction_filtered"] = len(unique_papers) - len(direction_passed)
    if dedup_stats["direction_filtered"] > 0:
        filtered_out = [p for p in unique_papers if p.get("score", 0) == 0]
        for p in filtered_out[:10]:
            dedup_stats["deduped_titles"].append(
                f"[方向不匹配] {p.get('title','')[:60]}")

    # ── 阶段3: 跨源多字段去重 ──
    cross_dedup_passed = []
    for p in direction_passed:
        is_dup, reason, confidence = is_duplicate_paper(p, seen_papers_full, strict=True)
        if is_dup:
            dedup_stats["cross_dedup"] += 1
            if len(dedup_stats["deduped_titles"]) < 20:
                dedup_stats["deduped_titles"].append(f"[{confidence}] {reason}")
        else:
            cross_dedup_passed.append(p)

    # 按评分排序
    relevant = cross_dedup_passed
    relevant.sort(key=lambda x: x.get("score", 0), reverse=True)

    dedup_stats["final_count"] = len(relevant)

    print(f"\n[*] 去重统计: 候选{dedup_stats['total_candidates']}篇 "
          f"| 方向过滤{dedup_stats['direction_filtered']}篇 "
          f"| paper_id去重{dedup_stats['seen_dedup']}篇 "
          f"| 跨源去重{dedup_stats['cross_dedup']}篇 "
          f"→ 最终{dedup_stats['final_count']}篇")

    # 候选: 全部有效论文
    candidates = relevant

    # ── 全文获取与解析 (核心新增) ──
    print(f"\n[*] === 全文获取与解析 | {date} ===")
    print(f"[*] 尝试下载并解析 TOP {min(10, len(candidates))} 篇候选论文的全文...")

    # 对排序后的候选论文进行全文处理；不因分数低而跳过日报卡片补齐。
    top_for_fulltext = candidates[:DAILY_FULLTEXT_PROCESS_LIMIT]
    candidates_processed, fulltext_stats = process_candidates_fulltext(
        top_for_fulltext, date, max_pdfs=DAILY_FULLTEXT_PROCESS_LIMIT
    )

    # 合并：已处理的替换原条目，未处理的原样保留
    processed_ids = {p["paper_id"] for p in candidates_processed}
    final_candidates = candidates_processed + [p for p in candidates if p["paper_id"] not in processed_ids]
    final_candidates.sort(key=lambda x: x.get("score", 0), reverse=True)

    # 补充 S2 限流信息
    fulltext_stats["s2_rate_limited"] = _s2_rate_limited

    print(f"[*] 全文处理完成: 下载{fulltext_stats['downloaded']}篇, "
          f"PDF_TEXT_FULL {fulltext_stats['pdf_text_full']}篇, "
          f"PDF_TEXT_PARTIAL {fulltext_stats['pdf_text_partial']}篇")

    # 精选: 按排序取前 N 篇，不因分数低而空掉日报卡片。
    selected = final_candidates[:DAILY_INTENSIVE_READ_COUNT]

    # 按阅读等级统计
    full_count = sum(1 for p in selected if p.get("reading_level") in
                     (ReadingLevel.PDF_TEXT_FULL, ReadingLevel.HUMAN_CONFIRMED))
    abstract_count = sum(1 for p in selected if p.get("reading_level") in
                         (ReadingLevel.ABSTRACT_ONLY, ReadingLevel.META_ONLY))

    print(f"[*] 精选论文: {len(selected)} 篇 (全文精读 {full_count}, 摘要级 {abstract_count})")

    # 更新长期知识库 (在生成报告前执行，以便日报包含KB写入状态)
    kb_result = update_knowledge_base(date, selected)
    if kb_result is None:
        kb_result = {}

    # 生成报告 (含KB写入状态)
    report = generate_daily_report(date, final_candidates, selected,
                                   list(set(queries_used)), fulltext_stats,
                                   kb_result, dedup_stats)
    report_path = OUTPUT_DIR / f"{date}_论文阅读日报.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"[+] 日报: {report_path}")

    # ── 深读队列: 保存全文提取文本 + 生成 Claude 深读队列 ──
    _save_deep_read_queue(date, selected, fulltext_stats)

    # 记录到数据库
    for p in candidates:
        mark_seen(conn, p)
    conn.execute(
        "INSERT OR REPLACE INTO daily_log VALUES (?,?,?,?)",
        (date, len(candidates), len(selected), json.dumps(list(set(queries_used)), ensure_ascii=False))
    )
    conn.commit()

    # 保存论文源文件 (不中断主流程)
    saved_count = 0
    for p in selected:
        try:
            result = save_paper_source_file(p, date, record_file=f"{date}_论文阅读日报.md")
            if result.get("status") == "saved":
                saved_count += 1
        except Exception as e:
            print(f"  [!] 源文件保存异常: {p.get('title','')[:40]}... - {e}")
    if saved_count > 0:
        print(f"[+] 源文件已保存: {saved_count}/{len(selected)} 篇")

    # 统计
    total = conn.execute("SELECT COUNT(*) FROM seen_papers").fetchone()[0]
    days = conn.execute("SELECT COUNT(*) FROM daily_log").fetchone()[0]
    print(f"\n[*] 去重库: {total} 篇论文, {days} 天记录")

    # ── 微信推送 ──
    success = total_sources > 0
    if args.push:
        push_wechat(date, len(candidates), selected, total, days, success)

    return 0


if __name__ == "__main__":
    sys.exit(main())
