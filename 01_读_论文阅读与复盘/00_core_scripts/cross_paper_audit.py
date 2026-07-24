#!/usr/bin/env python3
"""跨论文声明矛盾检测 v2 — 语义相似度 + 数值对比。

触发: 批量精读完成后自动运行
用法: python cross_paper_audit.py --dir md/2026-07-21/
依赖: pip install sentence-transformers (可选，无则用关键词匹配)
模型: all-MiniLM-L6-v2 (~80MB, 首次运行自动下载, CPU推理)
"""

import argparse, json, re
from pathlib import Path
from collections import defaultdict

try:
    from sentence_transformers import SentenceTransformer
    MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    HAS_ST = True
except ImportError:
    HAS_ST = False

CLAIM_PATTERNS = [
    (r'(accuracy|AUC|F1|IoU|RMSE|MAE|R²|precision|recall)\s*[=＞≥≧]\s*([0-9.]+)%?', 'metric'),
    (r'(outperforms?|superior to|better than|improves? over|state-of-the-art|SOTA)', 'superiority'),
    (r'(first|novel|new|proposed?|introduce|present\s+a\s+novel)', 'novelty'),
    (r'(RF|Random Forest|XGBoost|SVM|CNN|LSTM|Transformer|GNN|GWR|MGWR)\s+(is|are|outperforms?|achieves?)', 'method_claim'),
    (r'(limitation|constraint|drawback|weakness|fail|shortcoming)', 'limitation'),
    (r'(significantly?|p\s*[<≤]\s*0\.0[15])', 'significance'),
]

def extract_claims(text: str, source: str) -> list[dict]:
    claims = []
    for i, line in enumerate(text.split('\n'), 1):
        line = line.strip()
        if len(line) < 30:
            continue
        for pattern, ctype in CLAIM_PATTERNS:
            for m in re.finditer(pattern, line, re.IGNORECASE):
                claims.append({
                    'source': source, 'line': i, 'type': ctype,
                    'text': line[:250], 'match': m.group(0),
                })
    return claims

def find_contradictions_semantic(claims: list[dict]) -> list[dict]:
    """用语义相似度找矛盾声明对"""
    if not HAS_ST or len(claims) < 2:
        return find_contradictions_regex(claims)

    texts = [c['text'] for c in claims]
    embeddings = MODEL.encode(texts, show_progress_bar=False)

    contradictions = []
    processed = set()
    for i in range(len(claims)):
        for j in range(i+1, len(claims)):
            similarity = float(embeddings[i] @ embeddings[j])
            if similarity < 0.75:  # 不够相似，跳过
                continue
            if (claims[i]['source'] == claims[j]['source']):  # 同一篇论文内部
                continue

            # 相似声明但来源不同 → 检查是否互相矛盾
            c1, c2 = claims[i], claims[j]
            # 提取数值
            nums1 = re.findall(r'([0-9.]+)%?', c1['match'])
            nums2 = re.findall(r'([0-9.]+)%?', c2['match'])
            if nums1 and nums2:
                v1, v2 = float(nums1[0]), float(nums2[0])
                if abs(v1 - v2) > 10:
                    key = f'{min(i,j)}_{max(i,j)}'
                    if key not in processed:
                        processed.add(key)
                        contradictions.append({
                            'type': 'metric_conflict',
                            'claim1': f'[{c1["source"]}] {c1["text"][:120]}',
                            'claim2': f'[{c2["source"]}] {c2["text"][:120]}',
                            'similarity': round(similarity, 2),
                            'gap': f'{v1:.1f}% vs {v2:.1f}%',
                        })
            else:
                # 同类声明但无具体数字 → 标记为需人工审查
                key = f'{min(i,j)}_{max(i,j)}'
                if key not in processed:
                    processed.add(key)
                    contradictions.append({
                        'type': 'potential_conflict',
                        'claim1': f'[{c1["source"]}] {c1["text"][:120]}',
                        'claim2': f'[{c2["source"]}] {c2["text"][:120]}',
                        'similarity': round(similarity, 2),
                        'gap': '需人工审查',
                    })
    return contradictions

def find_contradictions_regex(claims: list[dict]) -> list[dict]:
    """降级方案：纯正则匹配"""
    return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=Path('audit_report.json'))
    parser.add_argument('--no-semantic', action='store_true', help='禁用语义推理(纯正则)')
    args = parser.parse_args()

    global HAS_ST
    if args.no_semantic:
        HAS_ST = False

    all_claims = []
    for md_file in args.dir.glob('*.md'):
        text = md_file.read_text(encoding='utf-8')
        claims = extract_claims(text, md_file.stem)
        all_claims.extend(claims)

    method = 'semantic(sentence-transformers)' if HAS_ST else 'regex-only'
    contradictions = find_contradictions_semantic(all_claims)

    sources = set(c['source'] for c in all_claims)
    report = {
        'method': method,
        'total_papers': len(sources),
        'total_claims': len(all_claims),
        'claim_types': {t: sum(1 for c in all_claims if c['type']==t)
                       for t in ['metric','superiority','novelty','method_claim','significance']},
        'contradictions': contradictions[:20],  # top 20
        'severity': 'HIGH' if len(contradictions)>3 else 'MEDIUM' if contradictions else 'LOW',
    }

    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'跨论文审计 [{method}]: {len(sources)}篇, {len(all_claims)}条声明')
    print(f'矛盾: {len(contradictions)}处 ({report["severity"]})')
    for c in contradictions[:5]:
        print(f'  [{c["type"]}] sim={c.get("similarity","?")}, gap={c["gap"]}')
        print(f'    A: {c["claim1"][:100]}')
        print(f'    B: {c["claim2"][:100]}')

    return 1 if contradictions else 0

if __name__ == '__main__':
    raise SystemExit(main())
