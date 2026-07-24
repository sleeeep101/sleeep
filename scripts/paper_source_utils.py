#!/usr/bin/env python3
"""paper_source_utils.py -- 论文源文件保存/索引公共工具

被 daily_paper_curator.py 和 backfill_paper_sources.py 共用。
"""

import csv
import hashlib
import json
import os
import re
import ssl
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# ── 路径 ────────────────────────────────────────────────

def _load_paper_sources_root():
    config_file = Path(__file__).resolve().parent.parent / "config" / "paths.json"
    try:
        import json as _json
        cfg = _json.loads(config_file.read_text(encoding="utf-8"))
        aw = cfg["academic_workflow"]
        return Path(aw["root"]) / aw["paper_sources"]
    except Exception:
        return Path("<LOCAL_PATH>")

PAPER_SOURCES_ROOT = _load_paper_sources_root()
MANIFEST_DIR = PAPER_SOURCES_ROOT / "_manifest"
INDEX_CSV = MANIFEST_DIR / "paper_source_index.csv"
MISSING_MD = MANIFEST_DIR / "missing_sources.md"

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# ── 工具函数 ─────────────────────────────────────────────

def sanitize_filename(name: str, max_len: int = 80) -> str:
    """清理 Windows 非法文件名字符，截断过长名称"""
    illegal = r'[<>:"/\\|?*\x00-\x1f]'
    clean = re.sub(illegal, "_", name)
    clean = re.sub(r"\s+", "_", clean)
    clean = clean.strip("._")
    if len(clean) > max_len:
        clean = clean[:max_len].rstrip("._")
    return clean or "unnamed"


def make_paper_slug(paper: Dict) -> str:
    """从论文元数据生成可读 slug"""
    title = paper.get("title", "unnamed")
    first_author = paper.get("first_author", paper.get("authors", ["unknown"])[0] if paper.get("authors") else "unknown")
    author_last = first_author.split()[-1] if first_author else "unknown"
    year = paper.get("year", "")[:4]

    words = [w for w in re.findall(r"[a-zA-Z0-9]+", title) if len(w) > 2 and w.lower() not in {
        "the", "and", "for", "with", "from", "using", "based", "analysis", "method",
        "study", "data", "spatial", "model", "learning", "deep", "approach",
    }]
    # 取前2个关键词以减少slug碰撞
    key_words = "_".join(words[:2]) if len(words) >= 2 else (words[0] if words else "paper")
    slug = f"{author_last}_{year}_{key_words}"
    return sanitize_filename(slug, max_len=100)


def compute_sha256(file_path: Path) -> str:
    """计算文件 SHA256"""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_index_csv():
    """确保索引 CSV 存在且有表头"""
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX_CSV.exists():
        INDEX_CSV.write_text(
            "date,title,doi,arxiv_id,url,source_type,local_path,"
            "status,reason,sha256,downloaded_at,record_file\n",
            encoding="utf-8")


def append_index_row(row: Dict):
    """追加一行到索引 CSV"""
    ensure_index_csv()
    fieldnames = [
        "date", "title", "doi", "arxiv_id", "url", "source_type",
        "local_path", "status", "reason", "sha256", "downloaded_at", "record_file",
    ]
    with open(INDEX_CSV, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(row)


def index_exists(title: str, doi: str, arxiv_id: str) -> bool:
    """检查索引中是否已有相同论文"""
    if not INDEX_CSV.exists():
        return False
    with open(INDEX_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # DOI 匹配
            if doi and row.get("doi", "") == doi:
                return True
            # arXiv ID 匹配
            if arxiv_id and row.get("arxiv_id", "") == arxiv_id:
                return True
            # 标题高度相似 (简单包含检查)
            existing_title = row.get("title", "").lower().strip()
            if len(title) > 20 and len(existing_title) > 20:
                # 取前 60 字符比较
                if title.lower().strip()[:60] == existing_title[:60]:
                    return True
    return False


def append_missing(paper: Dict, reason: str):
    """记录无法保存的论文到 missing_sources.md"""
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    if not MISSING_MD.exists():
        MISSING_MD.write_text(
            "# 缺失源文件记录\n\n"
            "> 记录所有无法获取开放源文件的论文。\n\n"
            "| 日期 | 标题 | DOI/arXiv | 原因 |\n"
            "|------|------|-----------|------|\n",
            encoding="utf-8")

    title = paper.get("title", "Unknown")[:80]
    date = paper.get("date", datetime.now().strftime("%Y-%m-%d"))
    doi = paper.get("doi", "")
    arxiv_id = paper.get("arxiv_id", "")
    identifier = doi or arxiv_id or paper.get("url", "")[:60]

    with open(MISSING_MD, "a", encoding="utf-8") as f:
        f.write(f"| {date} | {title} | {identifier} | {reason} |\n")


# ── HTTP 下载 ────────────────────────────────────────────

def download_file(url: str, dest: Path, timeout: int = 60) -> bool:
    """下载文件到 dest，成功返回 True"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperSourceArchiver/1.0"})
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
                    data = resp.read()
                    # 检查是否是真实 PDF (前4字节应为 %PDF)
                    if url.lower().endswith(".pdf") or dest.suffix == ".pdf":
                        if not data.startswith(b"%PDF"):
                            if attempt == 0:
                                continue  # 重试
                            return False
                    dest.write_bytes(data)
                    return True
            except Exception:
                if attempt < 1:
                    time.sleep(3)
                else:
                    raise
    except Exception:
        return False
    return False


def save_html_page(url: str, dest: Path, timeout: int = 45) -> bool:
    """下载论文页面 HTML，非空才算成功 (JS动态页面会返回空壳)"""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            # 拒绝少于 500 字节的空壳页面
            if len(html) < 500:
                return False
            # 只保留前 500KB
            if len(html) > 500000:
                html = html[:500000] + "\n<!-- truncated -->"
            dest.write_text(html, encoding="utf-8")
            return True
    except Exception:
        return False


# ── 核心保存函数 ─────────────────────────────────────────

def save_paper_source_file(paper: Dict, date: str,
                           output_root: Optional[Path] = None,
                           record_file: str = "") -> Dict:
    """保存一篇论文的源文件。

    1. 优先保存合法可访问的 PDF
    2. PDF 不可用时保存 HTML
    3. 都不行则至少保存 metadata.json + source.url
    4. 更新 paper_source_index.csv
    5. 失败时写入 missing_sources.md（不抛异常）

    返回 status dict。
    """
    if output_root is None:
        output_root = PAPER_SOURCES_ROOT

    title = paper.get("title", "Unknown").strip()
    doi = paper.get("doi", "").strip()
    arxiv_id = paper.get("arxiv_id", "").strip().rstrip("|").strip()
    url = paper.get("url", "").strip()
    pdf_url = paper.get("pdf_url", "").strip()

    result = {
        "title": title,
        "status": "skipped",
        "source_type": "missing",
        "local_path": "",
        "reason": "",
    }

    # 检查是否已存在
    if index_exists(title, doi, arxiv_id):
        result["status"] = "exists"
        result["reason"] = "已在索引中"
        return result

    # 创建目录（碰撞检测：已有不同论文占用同一slug时追加后缀）
    slug = make_paper_slug(paper)
    paper_dir = output_root / date / slug
    if paper_dir.exists():
        existing_meta = paper_dir / "metadata.json"
        if existing_meta.exists():
            try:
                existing = json.loads(existing_meta.read_text(encoding="utf-8"))
                existing_title = existing.get("title", "")
                if existing_title.lower().strip()[:60] != title.lower().strip()[:60]:
                    # slug碰撞：追加后缀
                    for n in range(2, 100):
                        alt_slug = f"{slug}_{n}"
                        alt_dir = output_root / date / alt_slug
                        if not alt_dir.exists():
                            slug = alt_slug
                            paper_dir = alt_dir
                            break
            except Exception:
                pass
    paper_dir.mkdir(parents=True, exist_ok=True)

    try:
        pdf_saved = False
        html_saved = False

        # ── 1. 尝试 PDF ──
        pdf_dest = paper_dir / "source.pdf"
        if pdf_url and not pdf_dest.exists():
            if download_file(pdf_url, pdf_dest):
                pdf_saved = True
                result["source_type"] = "pdf"
                result["local_path"] = str(pdf_dest.relative_to(output_root.parent))
                result["sha256"] = compute_sha256(pdf_dest)

        # ── 2. 尝试 HTML ──
        html_dest = paper_dir / "source.html"
        if not pdf_saved and url and not html_dest.exists():
            if save_html_page(url, html_dest):
                html_saved = True
                result["source_type"] = "html"
                result["local_path"] = str(html_dest.relative_to(output_root.parent))
                result["sha256"] = compute_sha256(html_dest)

        # ── 3. 保存 metadata.json ──
        meta_dest = paper_dir / "metadata.json"
        if not meta_dest.exists():
            metadata = {
                "title": title,
                "authors": paper.get("authors", []),
                "first_author": paper.get("first_author", ""),
                "year": paper.get("year", ""),
                "source": paper.get("source", ""),
                "doi": doi,
                "arxiv_id": arxiv_id,
                "url": url,
                "pdf_url": pdf_url,
                "abstract": paper.get("abstract", "")[:2000],
                "keywords": paper.get("keywords", ""),
                "category": paper.get("category", ""),
                "date": date,
                "downloaded_at": datetime.now().isoformat(),
                "source_type": result["source_type"],
            }
            meta_dest.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            if not result["local_path"]:
                result["local_path"] = str(meta_dest.relative_to(output_root.parent))
                result["source_type"] = "metadata_only"

        # ── 4. 保存 source.url (Windows Internet Shortcut 格式) ──
        url_dest = paper_dir / "source.url"
        if not url_dest.exists():
            urls = [u for u in [url, pdf_url, f"https://doi.org/{doi}" if doi else "",
                                f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""] if u]
            if urls:
                primary = urls[0]
                extra = urls[1:]
                lines = ["[InternetShortcut]", f"URL={primary}"]
                for e in extra:
                    lines.append(f"; {e}")
                url_dest.write_text("\n".join(lines), encoding="utf-8")

        # ── 5. 保存 note.md ──
        note_dest = paper_dir / "note.md"
        if not note_dest.exists():
            status_text = {
                "pdf": "已保存 PDF",
                "html": "已保存 HTML",
                "metadata_only": "仅保存元数据",
            }.get(result["source_type"], "未找到源文件")
            note_dest.write_text(
                f"# {title}\n\n"
                f"- 日期: {date}\n"
                f"- 来源: {paper.get('source', '')}\n"
                f"- DOI: {doi or '无'}\n"
                f"- arXiv: {arxiv_id or '无'}\n"
                f"- 保存状态: {status_text}\n"
                f"- 保存时间: {datetime.now().isoformat()}\n",
                encoding="utf-8")

        # ── 6. 更新索引 ──
        status = "saved" if result["source_type"] in ("pdf", "html") else "saved"
        if result["source_type"] == "metadata_only":
            status = "saved"

        append_index_row({
            "date": date,
            "title": title[:200],
            "doi": doi,
            "arxiv_id": arxiv_id,
            "url": url,
            "source_type": result["source_type"],
            "local_path": result["local_path"],
            "status": status,
            "reason": "",
            "sha256": result.get("sha256", ""),
            "downloaded_at": datetime.now().isoformat(),
            "record_file": record_file,
        })

        result["status"] = "saved"
        if not pdf_saved and not html_saved:
            result["reason"] = "PDF/HTML均不可用，仅保存元数据"

    except Exception as e:
        result["status"] = "failed"
        result["reason"] = str(e)[:200]
        append_missing(paper, f"保存异常: {e}")

    return result


def get_source_status_line(paper: Dict, date: str,
                           output_root: Optional[Path] = None) -> str:
    """生成日报中的源文件状态行"""
    if output_root is None:
        output_root = PAPER_SOURCES_ROOT

    slug = make_paper_slug(paper)
    paper_dir = output_root / date / slug
    pdf_path = paper_dir / "source.pdf"
    html_path = paper_dir / "source.html"
    meta_path = paper_dir / "metadata.json"

    if pdf_path.exists():
        rel = pdf_path.relative_to(output_root.parent)
        return f"本地源文件：已保存 {rel}"
    elif html_path.exists():
        rel = html_path.relative_to(output_root.parent)
        return f"本地源文件：已保存 {rel}"
    elif meta_path.exists():
        return "本地源文件：未找到开放 PDF，已记录 source.url 与 metadata.json"
    else:
        return "本地源文件：未找到"
