#!/usr/bin/env python3
"""fulltext_utils.py -- PDF/HTML全文下载 + 正文解析 + 阅读等级判定

集成到 daily_paper_curator.py 的搜索→筛选→全文获取→日报生成流水线。

依赖:
  - pdftotext (Poppler) 用于 PDF 文本提取
  - 备选: pypdf (纯 Python, 无需外部依赖)
  - requests + urllib 用于下载
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import ssl
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── 路径 ────────────────────────────────────────────────────

def _load_fulltext_root():
    config_file = Path(__file__).resolve().parent.parent / "config" / "paths.json"
    try:
        import json as _json
        cfg = _json.loads(config_file.read_text(encoding="utf-8"))
        aw = cfg["academic_workflow"]
        return Path(aw["root"]) / aw["fulltext_papers"]
    except Exception:
        return Path("<LOCAL_PATH>")

FULLTEXT_ROOT = _load_fulltext_root()

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


# ═══════════════════════════════════════════════════════════════
# 1. URL 解析 — 找到可用的全文链接
# ═══════════════════════════════════════════════════════════════

def resolve_fulltext_url(paper: Dict) -> Dict:
    """解析论文的全文 URL，返回优先级排序的候选链接列表。

    Returns:
        {"urls": [(url, source_type, priority), ...], "best": url or ""}
        source_type: "arxiv_pdf" | "s2_openaccess" | "doi_open" | "html_page" | "unknown"
    """
    candidates = []

    # 1. arXiv PDF (最高优先级)
    arxiv_id = paper.get("arxiv_id", "").strip()
    if arxiv_id:
        arxiv_id_clean = arxiv_id.replace("http://arxiv.org/abs/", "").replace("arxiv:", "")
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id_clean}.pdf"
        candidates.append((pdf_url, "arxiv_pdf", 100))

    # 2. 显式 pdf_url
    pdf_url = paper.get("pdf_url", "").strip()
    if pdf_url and pdf_url not in [u for u, _, _ in candidates]:
        if any(pdf_url.lower().endswith(ext) for ext in [".pdf", "/pdf"]):
            candidates.append((pdf_url, "explicit_pdf", 90))

    # 3. Semantic Scholar openAccessPdf
    if paper.get("is_oa") and paper.get("pdf_url"):
        s2_pdf = paper["pdf_url"].strip()
        if s2_pdf not in [u for u, _, _ in candidates]:
            candidates.append((s2_pdf, "s2_openaccess", 80))

    # 4. DOI → 开放期刊 PDF
    doi = paper.get("doi", "").strip()
    if doi:
        doi_clean = doi.replace("https://doi.org/", "")
        # MDPI, Frontiers, Nature SciRep, IWA 等开放期刊
        open_publishers = ["mdpi", "frontiersin", "nature.com/srep", "iwaponline",
                          "plos", "biomedcentral", "hindawi", "copernicus",
                          "springeropen", "wiley.com/doi/pdf"]
        for pub in open_publishers:
            if pub in doi:
                doi_pdf = f"https://doi.org/{doi_clean}"
                candidates.append((doi_pdf, "doi_open", 70))
                break

    # 5. HTML 页面作为最后手段
    url = paper.get("url", "").strip()
    if url and url not in [u for u, _, _ in candidates]:
        candidates.append((url, "html_page", 50))

    candidates.sort(key=lambda x: x[2], reverse=True)

    return {
        "urls": candidates,
        "best": candidates[0][0] if candidates else "",
        "has_arxiv": any(t == "arxiv_pdf" for _, t, _ in candidates),
        "has_explicit": any(t == "explicit_pdf" for _, t, _ in candidates),
        "has_any": len(candidates) > 0,
    }


# ═══════════════════════════════════════════════════════════════
# 2. 下载 — 下载 PDF 或 HTML 到本地
# ═══════════════════════════════════════════════════════════════

def download_fulltext(paper: Dict, date: str) -> Dict:
    """下载论文全文到本地目录。

    下载逻辑:
      1. 优先 arXiv PDF
      2. 其次显式 pdf_url
      3. 最后 HTML 页面

    Returns:
        {"status": "downloaded"|"failed"|"no_url",
         "local_path": str or "",
         "source_type": "pdf"|"html"|"",
         "error": str or ""}
    """
    fulltext_info = resolve_fulltext_url(paper)
    if not fulltext_info["has_any"]:
        return {"status": "no_url", "local_path": "", "source_type": "", "error": "无可用的全文链接"}

    # 创建目标目录
    safe_title = _safe_filename(paper.get("title", "unnamed"), max_len=60)
    paper_id = paper.get("paper_id", datetime.now().strftime("%H%M%S"))
    date_dir = FULLTEXT_ROOT / date
    date_dir.mkdir(parents=True, exist_ok=True)

    # 尝试每种 URL
    for url, source_type, priority in fulltext_info["urls"]:
        ext = ".pdf" if source_type in ("arxiv_pdf", "explicit_pdf", "s2_openaccess", "doi_open") else ".html"
        dest = date_dir / f"{paper_id}_{safe_title}{ext}"

        try:
            if ext == ".pdf":
                success = _download_file(url, dest)
            else:
                success = _download_html(url, dest)

            if success:
                # 验证文件非空
                if dest.stat().st_size > 100:
                    return {
                        "status": "downloaded",
                        "local_path": str(dest),
                        "source_type": source_type,
                        "error": "",
                        "url_used": url,
                        "file_size": dest.stat().st_size,
                    }
        except Exception as e:
            continue

    return {"status": "failed", "local_path": "", "source_type": "", "error": "所有URL下载失败"}


def _download_file(url: str, dest: Path, timeout: int = 120) -> bool:
    """下载文件，支持 PDF"""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AcademicPaperBot/1.0"
        })
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
                    data = resp.read()
                # PDF 魔数检查
                if dest.suffix == ".pdf" and not data.startswith(b"%PDF"):
                    if attempt < 1:
                        time.sleep(3)
                        continue
                    # 可能是重定向到登录页，保存但标记
                    dest.write_bytes(data)
                    return len(data) > 500
                dest.write_bytes(data)
                return True
            except Exception as e:
                if attempt < 1:
                    time.sleep(5)
                else:
                    raise e
    except Exception:
        return False
    return False


def _download_html(url: str, dest: Path, timeout: int = 60) -> bool:
    """下载 HTML 页面"""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        if len(html) < 500:
            return False
        if len(html) > 500000:
            html = html[:500000]
        dest.write_text(html, encoding="utf-8")
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════
# 3. 正文提取
# ═══════════════════════════════════════════════════════════════

def extract_text_from_pdf(pdf_path: str) -> Dict:
    """从 PDF 提取文本。

    Returns:
        {"status": "ok"|"failed",
         "text": str,
         "text_length_chars": int,
         "text_length_words": int,
         "method": "pdftotext"|"pypdf"|"none",
         "error": str}
    """
    path = Path(pdf_path)
    if not path.exists():
        return _extraction_error("PDF文件不存在")

    # 方法1: pdftotext (推荐)
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", "-nopgbrk", str(path), "-"],
            capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace"
        )
        if result.returncode == 0 and len(result.stdout.strip()) > 100:
            text = result.stdout.strip()
            return _build_extraction_result(text, method="pdftotext")
        stderr = result.stderr[:200] if result.stderr else ""
        if stderr:
            pass  # fall through to next method
    except FileNotFoundError:
        pass
    except Exception as e:
        pass

    # 方法2: pypdf (备选)
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
        text = "\n\n".join(pages)
        if len(text.strip()) > 100:
            return _build_extraction_result(text, method="pypdf")
    except ImportError:
        pass
    except Exception as e:
        pass

    # 方法3: PyPDF2
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(str(path))
        pages = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
        text = "\n\n".join(pages)
        if len(text.strip()) > 100:
            return _build_extraction_result(text, method="PyPDF2")
    except ImportError:
        pass
    except Exception as e:
        pass

    return _extraction_error("所有PDF提取方法均失败 (pdftotext/pypdf/PyPDF2 不可用)")


def extract_text_from_html(html_path: str) -> Dict:
    """从 HTML 页面提取正文文本。

    尝试去除导航/页脚/样式等噪声，保留论文正文。
    """
    path = Path(html_path)
    if not path.exists():
        return _extraction_error("HTML文件不存在")

    try:
        html = path.read_text(encoding="utf-8", errors="replace")

        # 移除 script, style, nav, footer, header
        for tag in ["script", "style", "nav", "footer", "header", "aside",
                     "noscript", "iframe", "form"]:
            html = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", html, flags=re.DOTALL | re.IGNORECASE)

        # 移除 HTML 标签
        text = re.sub(r"<[^>]+>", " ", html)
        # 移除多余空白
        text = re.sub(r"\s+", " ", text)
        # 移除常见噪声行
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        text = "\n".join(lines)

        if len(text) > 200:
            return _build_extraction_result(text, method="html_strip")
        return _extraction_error("HTML正文提取后文本过短 (<200字符)")
    except Exception as e:
        return _extraction_error(f"HTML提取异常: {str(e)[:200]}")


def _build_extraction_result(text: str, method: str) -> Dict:
    return {
        "status": "ok",
        "text": text,
        "text_length_chars": len(text),
        "text_length_words": len(text.split()),
        "method": method,
        "error": "",
    }


def _extraction_error(msg: str) -> Dict:
    return {
        "status": "failed",
        "text": "",
        "text_length_chars": 0,
        "text_length_words": 0,
        "method": "none",
        "error": msg,
    }


# ═══════════════════════════════════════════════════════════════
# 4. 章节检测
# ═══════════════════════════════════════════════════════════════

def parse_fulltext_sections(text: str) -> Dict:
    """检测学术论文的标准章节。

    通过正则匹配章节标题模式 (如 "1. Introduction", "2. Methods", "Abstract" 等)。
    """
    if not text or len(text) < 100:
        return _empty_sections()

    # 常见章节标题模式 (大小写不敏感)
    section_patterns = {
        "abstract": [
            r"(?i)^\s*(abstract|a\s*b\s*s\s*t\s*r\s*a\s*c\s*t)\s*$",
            r"(?i)^\s*abstract\b",
        ],
        "introduction": [
            r"(?i)^\s*(\d+\.?\s*)?intro(d(u(c(t(i(o(n)?)?)?)?)?)?)?\s*$",
            r"(?i)^\s*(\d+\.?\s*)?introduction\b",
            r"(?i)^\s*(\d+\.?\s*)?background\b",
        ],
        "methods": [
            r"(?i)^\s*(\d+\.?\s*)?(methods?|methodology)\s*$",
            r"(?i)^\s*(\d+\.?\s*)?materials?\s*(and|&)\s*methods?\s*$",
            r"(?i)^\s*(\d+\.?\s*)?data\s*(and|&)\s*methods?\s*$",
            r"(?i)^\s*(\d+\.?\s*)?experimental\s*(setup|design)\s*$",
            r"(?i)^\s*(\d+\.?\s*)?study\s*area\b",
        ],
        "results": [
            r"(?i)^\s*(\d+\.?\s*)?results?\s*(and|&)\s*discussion\s*$",
            r"(?i)^\s*(\d+\.?\s*)?results?\s*$",
            r"(?i)^\s*(\d+\.?\s*)?experiments?\s*(and|&)\s*results?\s*$",
            r"(?i)^\s*(\d+\.?\s*)?(experiments?|evaluation)\s*$",
            r"(?i)^\s*(\d+\.?\s*)?case\s*stud(y|ies)\s*$",
        ],
        "discussion": [
            r"(?i)^\s*(\d+\.?\s*)?discussion\s*$",
            r"(?i)^\s*(\d+\.?\s*)?discussion\s*(and|&)\s*conclusion\s*$",
        ],
        "conclusion": [
            r"(?i)^\s*(\d+\.?\s*)?conclusion(s)?\s*$",
            r"(?i)^\s*(\d+\.?\s*)?conclusion\s*(and|&)\s*(future\s*)?(work|outlook)\s*$",
            r"(?i)^\s*(\d+\.?\s*)?summary\s*$",
        ],
        "references": [
            r"(?i)^\s*(references|bibliography|literature\s*cited)\s*$",
            r"(?i)^\s*(\d+\.?\s*)?references?\s*$",
        ],
    }

    detected = {}
    lines = text.split("\n")
    for section_name, patterns in section_patterns.items():
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) > 120:
                continue
            for pat in patterns:
                if re.match(pat, line):
                    if section_name not in detected:
                        detected[section_name] = {
                            "found": True,
                            "line_number": i + 1,
                            "heading": line[:80],
                        }
                    break
            if section_name in detected:
                break

    # 也检查全文中是否包含关键词 (更宽松的检测)
    text_lower = text.lower()
    loose_keywords = {
        "abstract": ["abstract"],
        "introduction": ["introduction"],
        "methods": ["method", "methodology", "materials and methods"],
        "results": ["result", "experiment"],
        "discussion": ["discussion"],
        "conclusion": ["conclusion", "concluding remarks"],
        "references": ["references", "bibliography"],
    }
    for section_name, keywords in loose_keywords.items():
        if section_name not in detected:
            for kw in keywords:
                if kw in text_lower:
                    detected[section_name] = {"found": True, "line_number": -1, "heading": f"(关键词: {kw})"}
                    break

    has_abstract = "abstract" in detected
    has_introduction = "introduction" in detected
    has_methods_or_data = "methods" in detected
    has_results_or_case = "results" in detected
    has_discussion_or_conclusion = "discussion" in detected or "conclusion" in detected

    # 计算覆盖的关键章节数
    key_sections = ["abstract", "introduction", "methods", "results", "discussion", "conclusion"]
    covered = sum(1 for s in key_sections if s in detected)

    # 是否是纯参考文献/摘要
    is_pure_references = len(detected) <= 2 and ("references" in detected)
    is_only_abstract = len(detected) <= 1 and has_abstract

    return {
        "detected_sections": list(detected.keys()),
        "section_count": len(detected),
        "key_sections_covered": covered,
        "has_abstract": has_abstract,
        "has_introduction": has_introduction,
        "has_methods_or_data": has_methods_or_data,
        "has_results_or_case": has_results_or_case,
        "has_discussion_or_conclusion": has_discussion_or_conclusion,
        "is_pure_references": is_pure_references,
        "is_only_abstract": is_only_abstract,
        "section_details": detected,
    }


def _empty_sections() -> Dict:
    return {
        "detected_sections": [],
        "section_count": 0,
        "key_sections_covered": 0,
        "has_abstract": False,
        "has_introduction": False,
        "has_methods_or_data": False,
        "has_results_or_case": False,
        "has_discussion_or_conclusion": False,
        "is_pure_references": False,
        "is_only_abstract": False,
        "section_details": {},
    }


# ═══════════════════════════════════════════════════════════════
# 4.5 中文文本质量检测
# ═══════════════════════════════════════════════════════════════

def chinese_text_quality_check(text: str) -> Dict:
    """检测提取文本中的中文编码损坏/乱码/OCR失败。

    判断条件:
      - 提取字符数过低 (<500)
      - 中文字符比例异常低 (文本>100字但中文<5%)
      - 出现大量乱码符号 (□, 䈀, 等CJK兼容区异常字符)
      - 重复无意义字符过多
      - 标题/摘要/方法/结果等中文关键词完全缺失
      - 异常短行比例过高 (>50%行<10字符)

    Returns:
        {"quality": "ok"|"suspicious"|"corrupted",
         "issues": [str,...],
         "chinese_char_ratio": float,
         "garbled_char_count": int,
         "short_line_ratio": float}
    """
    issues = []
    text_len = len(text)

    if text_len < 100:
        return {"quality": "corrupted", "issues": ["文本过短 (<100字符)"],
                "chinese_char_ratio": 0.0, "garbled_char_count": 0, "short_line_ratio": 1.0}

    # 中文字符比例
    chinese_chars = len(re.findall(r'[一-鿿㐀-䶿]', text))
    chinese_ratio = chinese_chars / max(text_len, 1)

    # 乱码字符检测 (CJK统一表意文字扩展区 + 疑似编码损坏的符号)
    garbled_patterns = [
        r'[�]',           # 替换字符 �
        r'[■-◿]',    # 几何图形方块 □▣▤
        r'[À-ÿ]{4,}', # 连续拉丁扩展字符(GBK/GB2312错解码常见)
        r'[\x80-\x9f]{2,}',    # C1控制字符
    ]
    garbled_count = 0
    for pat in garbled_patterns:
        garbled_count += len(re.findall(pat, text))

    # 重复无意义字符
    repeat_ratio = 0.0
    if text_len > 200:
        lines = text.split('\n')
        unique_chars = len(set(text))
        if unique_chars / max(text_len, 1) < 0.05:
            issues.append(f"字符多样性极低 ({unique_chars}唯一字符/{text_len}总字符)")
            repeat_ratio = 1.0

    # 异常短行比例
    lines = text.split('\n')
    short_lines = [l for l in lines if 0 < len(l.strip()) < 10]
    short_line_ratio = len(short_lines) / max(len(lines), 1)
    if short_line_ratio > 0.5:
        issues.append(f"短行比例过高 ({short_line_ratio:.0%}, {len(short_lines)}/{len(lines)}行)")

    # 中文关键词检查
    cn_keywords = ['摘要', '方法', '结果', '讨论', '结论', '引言',
                   '研究', '数据', '分析', '实验', '模型', '参考文献']
    missing_keywords = [kw for kw in cn_keywords if kw not in text]
    if len(missing_keywords) >= 8:
        issues.append(f"中文章节关键词大量缺失 (缺失{len(missing_keywords)}/{len(cn_keywords)}个)")

    # 判断
    if text_len < 500:
        issues.append(f"文本过短 ({text_len}字符)")
        quality = "corrupted"
    elif (text_len > 2000 and chinese_ratio < 0.05) or garbled_count > 50:
        quality = "corrupted"
        if text_len > 2000 and chinese_ratio < 0.05:
            issues.append(f"中文比例异常低 ({chinese_ratio:.1%})")
        if garbled_count > 50:
            issues.append(f"乱码字符过多 ({garbled_count}个)")
    elif garbled_count > 10 or short_line_ratio > 0.6 or (text_len > 2000 and chinese_ratio < 0.10):
        quality = "suspicious"
        issues.append(f"疑似编码损坏: garbled={garbled_count}, short_line={short_line_ratio:.1%}, cn_ratio={chinese_ratio:.1%}")
    else:
        quality = "ok"

    return {
        "quality": quality,
        "issues": issues,
        "chinese_char_ratio": round(chinese_ratio, 4),
        "garbled_char_count": garbled_count,
        "short_line_ratio": round(short_line_ratio, 4),
    }


# ═══════════════════════════════════════════════════════════════
# 5. 阅读等级判定
# ═══════════════════════════════════════════════════════════════

def classify_reading_level(paper: Dict, fulltext_result: Dict,
                           extraction_result: Dict,
                           sections: Dict) -> Tuple[str, Dict]:
    """根据实际全文证据判定阅读等级。

    Returns:
        (reading_level, evidence_report_dict)
    """
    evidence = {
        "download_status": fulltext_result.get("status", "unknown"),
        "download_error": fulltext_result.get("error", ""),
        "local_path": fulltext_result.get("local_path", ""),
        "extraction_status": extraction_result.get("status", "unknown"),
        "extraction_method": extraction_result.get("method", "none"),
        "extraction_error": extraction_result.get("error", ""),
        "text_length_chars": extraction_result.get("text_length_chars", 0),
        "text_length_words": extraction_result.get("text_length_words", 0),
        "sections": sections,
        "reading_level": "",
        "reason": "",
    }

    # 无全文链接 → META_ONLY 或 ABSTRACT_ONLY
    if fulltext_result.get("status") == "no_url":
        if paper.get("abstract", "").strip():
            evidence["reading_level"] = "ABSTRACT_ONLY"
            evidence["reason"] = "无可用全文链接，但有摘要"
        else:
            evidence["reading_level"] = "META_ONLY"
            evidence["reason"] = "无可用全文链接，无摘要"
        return evidence["reading_level"], evidence

    # 下载失败
    if fulltext_result.get("status") == "failed":
        evidence["reading_level"] = "ABSTRACT_ONLY"
        evidence["reason"] = f"全文下载失败: {fulltext_result.get('error', '未知错误')}"
        return evidence["reading_level"], evidence

    # 解析失败
    if extraction_result.get("status") == "failed":
        evidence["reading_level"] = "ABSTRACT_ONLY"
        evidence["reason"] = f"正文解析失败: {extraction_result.get('error', '未知错误')}"
        return evidence["reading_level"], evidence

    # 有正文，检查质量
    text_len_chars = extraction_result.get("text_length_chars", 0)
    text_len_words = extraction_result.get("text_length_words", 0)
    key_sections = sections.get("key_sections_covered", 0)

    # 质量要求:
    #   - ≥2000 英文单词 (约15000字符)
    #   - 或 ≥3000 中文字符
    #   - 至少覆盖3类关键章节
    #   - 必须有 methods_or_data
    #   - 必须有 results_or_case 或 discussion_or_conclusion

    has_min_length = text_len_words >= 2000 or text_len_chars >= 15000
    has_enough_sections = key_sections >= 3
    has_methods = sections.get("has_methods_or_data", False)
    has_results_or_discussion = sections.get("has_results_or_case", False) or \
        sections.get("has_discussion_or_conclusion", False)
    is_only_abstract = sections.get("is_only_abstract", False)

    if has_min_length and has_enough_sections and has_methods and has_results_or_discussion:
        if not is_only_abstract:
            evidence["reading_level"] = "PDF_TEXT_FULL"
            evidence["reason"] = (
                f"全文下载成功，正文{text_len_chars}字符/{text_len_words}词，"
                f"覆盖{key_sections}类关键章节（含方法+结果/讨论）"
            )
            return evidence["reading_level"], evidence

    # 部分正文
    if text_len_chars > 500:
        evidence["reading_level"] = "PDF_TEXT_PARTIAL"
        missing = []
        if not has_enough_sections:
            missing.append(f"仅覆盖{key_sections}类关键章节（需≥3）")
        if not has_min_length:
            missing.append(f"正文长度不足（{text_len_chars}字符/{text_len_words}词）")
        if not has_methods:
            missing.append("未检测到方法/数据章节")
        if not has_results_or_discussion:
            missing.append("未检测到结果/讨论/结论章节")
        if is_only_abstract:
            missing.append("正文仅含摘要")
        evidence["reason"] = "已下载全文但解析不完整: " + "; ".join(missing)
        return evidence["reading_level"], evidence

    # 正文太短
    if text_len_chars <= 500:
        evidence["reading_level"] = "ABSTRACT_ONLY"
        evidence["reason"] = f"PDF解析后正文过短（{text_len_chars}字符），仅同摘要级"
        return evidence["reading_level"], evidence

    evidence["reading_level"] = "PDF_TEXT_PARTIAL"
    evidence["reason"] = "已下载全文但未达到PDF_TEXT_FULL标准"
    return evidence["reading_level"], evidence


# ═══════════════════════════════════════════════════════════════
# 6. 主流水线 — 处理一篇论文的完整全文获取+分级
# ═══════════════════════════════════════════════════════════════

def process_paper_fulltext(paper: Dict, date: str,
                           skip_download: bool = False) -> Dict:
    """一篇论文的完整全文处理流水线。

    步骤: 解析URL → 下载 → 提取文本 → 检测章节 → 判定等级

    Args:
        paper: 论文元数据字典
        date: 日期字符串 YYYY-MM-DD
        skip_download: True 时仅检查本地已有文件，不重新下载

    Returns:
        返回 paper 本身的更新后的副本，增加以下字段:
          - reading_level
          - evidence_source
          - full_text_read
          - fulltext_local_path
          - fulltext_extraction_method
          - fulltext_text_length_chars
          - fulltext_text_length_words
          - fulltext_sections
          - fulltext_evidence_report
          - fulltext_download_status
          - fulltext_extraction_status
    """
    result_paper = dict(paper)

    # 初始化全文字段
    result_paper.setdefault("fulltext_local_path", "")
    result_paper.setdefault("fulltext_extraction_method", "none")
    result_paper.setdefault("fulltext_text_length_chars", 0)
    result_paper.setdefault("fulltext_text_length_words", 0)
    result_paper.setdefault("fulltext_sections", {})
    result_paper.setdefault("fulltext_evidence_report", {})
    result_paper.setdefault("fulltext_download_status", "not_attempted")
    result_paper.setdefault("fulltext_extraction_status", "not_attempted")

    # Step 1: 下载
    if not skip_download:
        ft_result = download_fulltext(paper, date)
    else:
        # 检查本地是否已有
        safe_title = _safe_filename(paper.get("title", "unnamed"), max_len=60)
        paper_id = paper.get("paper_id", "")
        date_dir = FULLTEXT_ROOT / date
        # 尝试找到已有文件
        existing = list(date_dir.glob(f"{paper_id}_*")) if date_dir.exists() else []
        if existing:
            ft_result = {
                "status": "downloaded",
                "local_path": str(existing[0]),
                "source_type": "pdf" if existing[0].suffix == ".pdf" else "html",
                "error": "",
                "url_used": "(本地已有)",
                "file_size": existing[0].stat().st_size,
            }
        else:
            ft_result = download_fulltext(paper, date)

    result_paper["fulltext_download_status"] = ft_result.get("status", "failed")
    local_path = ft_result.get("local_path", "")

    if ft_result.get("status") != "downloaded":
        result_paper["reading_level"] = "ABSTRACT_ONLY" if paper.get("abstract", "").strip() else "META_ONLY"
        result_paper["evidence_source"] = f"全文下载失败: {ft_result.get('error', '未知')}"
        result_paper["full_text_read"] = False
        return result_paper

    result_paper["fulltext_local_path"] = local_path

    # Step 2: 提取文本
    if local_path.lower().endswith(".pdf"):
        extraction = extract_text_from_pdf(local_path)
    else:
        extraction = extract_text_from_html(local_path)

    result_paper["fulltext_extraction_status"] = extraction.get("status", "failed")
    result_paper["fulltext_extraction_method"] = extraction.get("method", "none")
    result_paper["fulltext_text_length_chars"] = extraction.get("text_length_chars", 0)
    result_paper["fulltext_text_length_words"] = extraction.get("text_length_words", 0)

    # Step 3: 检测章节
    sections = parse_fulltext_sections(extraction.get("text", ""))
    result_paper["fulltext_sections"] = sections

    # Step 3.5: 中文文本质量检测
    extracted_text = extraction.get("text", "")
    cn_quality = {"quality": "ok", "issues": [], "chinese_char_ratio": 0, "garbled_char_count": 0, "short_line_ratio": 0}
    has_cn = bool(re.search(r'[一-鿿]', extracted_text))
    if has_cn and len(extracted_text) > 100:
        cn_quality = chinese_text_quality_check(extracted_text)
    result_paper["cn_text_quality"] = cn_quality

    # Step 4: 判定阅读等级
    reading_level, evidence = classify_reading_level(paper, ft_result, extraction, sections)

    # 中文编码损坏时降级阅读等级
    if cn_quality["quality"] == "corrupted":
        if reading_level == "PDF_TEXT_FULL":
            reading_level = "PDF_TEXT_PARTIAL"
            evidence["reason"] += f"; 中文编码严重损坏(ocr_needed): {'; '.join(cn_quality['issues'][:3])}"
            result_paper["cn_ocr_needed"] = True
        evidence["cn_quality"] = "corrupted"
    elif cn_quality["quality"] == "suspicious":
        evidence["cn_quality"] = "suspicious"
        result_paper["cn_quality_warning"] = True

    result_paper["reading_level"] = reading_level
    result_paper["evidence_source"] = f"全文{evidence.get('extraction_method', '?')}解析: {evidence.get('reason', '')}"
    result_paper["full_text_read"] = reading_level in ("PDF_TEXT_FULL", "HUMAN_CONFIRMED")
    result_paper["fulltext_evidence_report"] = evidence

    return result_paper


def _safe_filename(name: str, max_len: int = 60) -> str:
    """生成安全文件名"""
    illegal = r'[<>:"/\\|?*\x00-\x1f]'
    clean = re.sub(illegal, "_", name)
    clean = re.sub(r"\s+", "_", clean)
    clean = clean.strip("._")[:max_len]
    return clean or "unnamed"


# ═══════════════════════════════════════════════════════════════
# 7. 批量处理
# ═══════════════════════════════════════════════════════════════

def process_candidates_fulltext(candidates: List[Dict], date: str,
                                max_pdfs: int = 10) -> Tuple[List[Dict], Dict]:
    """批量处理候选论文的全文获取。

    Args:
        candidates: 候选论文列表
        date: 日期
        max_pdfs: 最多下载/处理的PDF数量 (避免过长时间)

    Returns:
        (updated_candidates, stats)
        stats: {"total":, "downloaded":, "pdf_text_full":, "pdf_text_partial":,
                "abstract_only":, "meta_only":, "download_failed":, "parse_failed":,
                "ocr_needed":}
    """
    stats = {
        "total": len(candidates),
        "attempted": 0,
        "downloaded": 0,
        "pdf_text_full": 0,
        "pdf_text_partial": 0,
        "abstract_only": 0,
        "meta_only": 0,
        "download_failed": 0,
        "parse_failed": 0,
        "ocr_needed": 0,
    }

    updated = []

    for paper in candidates:
        if stats["attempted"] >= max_pdfs:
            # 超过上限的不做全文处理
            updated.append(paper)
            continue

        stats["attempted"] += 1
        result = process_paper_fulltext(paper, date)
        updated.append(result)

        rl = result.get("reading_level", "")
        dl = result.get("fulltext_download_status", "")

        if dl == "downloaded":
            stats["downloaded"] += 1
        elif dl == "failed":
            stats["download_failed"] += 1

        if rl == "PDF_TEXT_FULL":
            stats["pdf_text_full"] += 1
        elif rl == "PDF_TEXT_PARTIAL":
            stats["pdf_text_partial"] += 1
        elif rl == "ABSTRACT_ONLY":
            stats["abstract_only"] += 1
        elif rl == "META_ONLY":
            stats["meta_only"] += 1

        if result.get("fulltext_extraction_status") == "failed" and dl == "downloaded":
            stats["parse_failed"] += 1

        if result.get("cn_ocr_needed") or result.get("cn_text_quality", {}).get("quality") == "corrupted":
            stats["ocr_needed"] += 1

        # 下载间隔
        if dl == "downloaded":
            time.sleep(2)

    return updated, stats
