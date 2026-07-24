"""Research-gap screening based on explicit, local topic evidence.

The tool never scans a personal knowledge graph unless a path is supplied.
It is a screening aid, not evidence that a research gap exists.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


DEFAULT_KG_PATH = (
    Path(__file__).resolve().parent.parent / "knowledge_graph" / "kg_data.json"
)


def normalise(value: str) -> str:
    """Return a comparable topic string while preserving the original elsewhere."""
    return " ".join(value.casefold().split())


def load_kg_topics(kg_path: Path) -> set[str]:
    """Load Paper-node topics from an explicitly selected JSON graph file.

    A missing file means no local evidence is available; it is not an error and
    must not be interpreted as a research gap.
    """
    if not kg_path.is_file():
        return set()

    with kg_path.open("r", encoding="utf-8") as file:
        graph = json.load(file)

    topics: set[str] = set()
    for node in graph.get("nodes", []):
        if node.get("entity_type") != "Paper":
            continue
        for topic in node.get("topics", []):
            if isinstance(topic, str) and normalise(topic):
                topics.add(normalise(topic))
    return topics


def _related_topics(keyword: str, topics: Iterable[str]) -> list[str]:
    """Find non-exact topic overlaps in a stable, reviewable order."""
    comparable = normalise(keyword)
    return sorted(
        topic
        for topic in topics
        if topic != comparable and (comparable in topic or topic in comparable)
    )


def detect_gaps(
    query_keywords: list[str],
    existing_topics: set[str],
    *,
    evidence_available: bool = True,
) -> dict:
    """Classify terms as exact, partial, or uncovered local evidence.

    ``gap_score`` is the proportion without *exact* local coverage only when
    an evidence source was actually loaded. Partial matches remain in this
    conservative score, because substring similarity is not proof that a paper
    addresses the same research question. With no source, a score is withheld.
    """
    exact: list[str] = []
    uncovered: list[str] = []
    partial_matches: list[dict[str, object]] = []
    normalised_topics = {normalise(topic) for topic in existing_topics if normalise(topic)}

    for keyword in query_keywords:
        if not isinstance(keyword, str) or not normalise(keyword):
            continue
        comparable = normalise(keyword)
        if comparable in normalised_topics:
            exact.append(keyword)
            continue

        uncovered.append(keyword)
        related = _related_topics(keyword, normalised_topics)
        if related:
            partial_matches.append({"keyword": keyword, "related": related[:5]})

    total = len(exact) + len(uncovered)
    gap_score = round(len(uncovered) / max(1, total), 2) if evidence_available else None
    if not evidence_available:
        recommendation = "No graph evidence was loaded; do not infer a research gap. Supply --kg-file or --use-default-kg."
    elif total == 0:
        recommendation = "No valid keywords supplied; do not infer a research gap."
    elif gap_score > 0.5:
        recommendation = "High local-evidence gap; verify with a documented literature search."
    elif partial_matches:
        recommendation = "Some related local evidence exists; compare methods, scale, place, and time before claiming novelty."
    else:
        recommendation = "Local coverage is relatively strong; refine the question and check external literature."

    return {
        "total_keywords": total,
        "covered": len(exact),
        "uncovered": uncovered,
        "partial_matches": partial_matches,
        "evidence_available": evidence_available,
        "gap_score": gap_score,
        "recommendation": recommendation,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("keywords", nargs="+", help="Keywords to screen")
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--kg-file",
        type=Path,
        help="An explicit exported graph JSON path; no graph is read by default.",
    )
    source_group.add_argument(
        "--use-default-kg",
        action="store_true",
        help="Opt in to the workflow-local sample/default graph path.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    kg_path = DEFAULT_KG_PATH if args.use_default_kg else args.kg_file
    evidence_available = bool(kg_path and kg_path.is_file())
    topics = load_kg_topics(kg_path) if evidence_available else set()
    result = detect_gaps(args.keywords, topics, evidence_available=evidence_available)

    print(f"Graph evidence loaded: {result['evidence_available']} | Local topics consulted: {len(topics)}")
    print(f"Keywords: {args.keywords}")
    print(
        f"Exact coverage: {result['covered']} | Uncovered: {len(result['uncovered'])} "
        f"| Partial matches: {len(result['partial_matches'])}"
    )
    score_text = str(result["gap_score"]) if result["gap_score"] is not None else "withheld"
    print(f"Gap score: {score_text} -> {result['recommendation']}")
    if result["uncovered"]:
        print(f"Uncovered keywords: {', '.join(result['uncovered'])}")
    for match in result["partial_matches"]:
        print(f"  {match['keyword']} -> related: {', '.join(match['related'][:3])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
