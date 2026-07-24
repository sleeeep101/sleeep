"""
PDF提取质量报告 + 自动降级策略
==============================
每次提取后自动运行，评估质量并决定是否需要升级引擎。
"""
import re, sys, os
from typing import Dict, Tuple

def assess_quality(text: str, engine: str, pages: int) -> Dict:
    """评估提取文本质量，返回评分和建议"""
    total = len(text)
    chinese = len(re.findall(r'[一-鿿]', text))
    chinese_ratio = chinese / max(1, total)
    chars_per_page = total / max(1, pages)

    # 乱码检测
    garbled = len(re.findall(r'[�□]', text))
    latin_garbled = len(re.findall(r'[-ÿ]{4,}', text))
    garbled_score = max(0, 1 - (garbled + latin_garbled) / max(1, total))

    # 中文质量
    if chinese_ratio > 0.3:
        lang_score = min(1.0, chinese_ratio / 0.6)
    else:
        lang_score = chinese_ratio / 0.3  # 英文论文

    # 密度评分
    if chars_per_page > 3000:
        density_score = 1.0
    elif chars_per_page > 1000:
        density_score = 0.7
    elif chars_per_page > 200:
        density_score = 0.4
    else:
        density_score = 0.1

    overall = (garbled_score * 0.4 + lang_score * 0.35 + density_score * 0.25)

    # 判定阅读等级
    if total >= 15000 and chinese_ratio > 0.2:
        level = "PDF_TEXT_FULL"
        confidence = "high" if overall > 0.7 else "medium"
    elif total >= 1000:
        level = "PDF_TEXT_PARTIAL"
        confidence = "medium" if overall > 0.5 else "low"
    elif total >= 100:
        level = "ABSTRACT_ONLY"
        confidence = "low"
    else:
        level = "META_ONLY"
        confidence = "low"

    # 建议下一步
    if overall < 0.3 and engine in ("pymupdf4llm", "pymupdf", "pypdf"):
        suggestion = "UPGRADE: 文字引擎质量不足，建议切换到 easyocr 或 tesseract OCR"
    elif overall < 0.4 and engine == "easyocr":
        suggestion = "UPGRADE: easyocr质量偏低，建议尝试 tesseract(中文)或提高DPI至300+"
    elif overall >= 0.7:
        suggestion = "OK: 质量合格，可直接入知识库"
    else:
        suggestion = "REVIEW: 建议人工抽查关键章节"

    return {
        "engine": engine,
        "pages": pages,
        "total_chars": total,
        "chinese_chars": chinese,
        "chinese_ratio": round(chinese_ratio, 3),
        "chars_per_page": round(chars_per_page, 0),
        "garbled_count": garbled + latin_garbled,
        "quality_score": round(overall, 3),
        "reading_level": level,
        "confidence": confidence,
        "suggestion": suggestion,
    }


def auto_degrade(quality: Dict, available_engines: list) -> Tuple[str, dict]:
    """根据质量自动选择降级/升级引擎"""
    engine = quality["engine"]
    score = quality["quality_score"]
    page_density = quality["chars_per_page"]

    # 规则1: 文字引擎无产出 → OCR
    if page_density < 50 and engine in ("pymupdf4llm", "pymupdf", "pypdf", "pdfplumber"):
        for candidate in ["easyocr", "tesseract"]:
            if candidate in available_engines:
                return candidate, {"reason": "文字层无内容，切换到OCR", "trigger": "empty_text"}

    # 规则2: easyocr质量差 → 提高DPI或切换tesseract
    if score < 0.3 and engine == "easyocr":
        if "tesseract" in available_engines:
            return "tesseract", {"reason": "easyocr中文识别率低，切换tesseract", "trigger": "low_quality_ocr"}
        return engine, {"reason": "建议提高DPI至300+重试", "dpi_hint": 300, "trigger": "low_quality_ocr"}

    # 规则3: tesseract质量差 → markitdown兜底
    if score < 0.25 and engine == "tesseract":
        if "markitdown" in available_engines:
            return "markitdown", {"reason": "OCR质量不足，尝试markitdown通用转换", "trigger": "ocr_failed"}

    return engine, {"reason": "当前引擎已是最佳选择"}


# CLI
if __name__ == "__main__":
    import argparse, json
    p = argparse.ArgumentParser()
    p.add_argument("--text-file", help="提取的文本文件路径")
    p.add_argument("--text", help="直接传入文本")
    p.add_argument("--engine", default="unknown")
    p.add_argument("--pages", type=int, default=1)
    args = p.parse_args()

    text = args.text or (open(args.text_file, encoding="utf-8").read() if args.text_file else "")
    result = assess_quality(text, args.engine, args.pages)
    print(json.dumps(result, ensure_ascii=False, indent=2))
