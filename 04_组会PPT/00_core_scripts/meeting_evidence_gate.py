"""Validate a structured academic group-meeting brief before presenting it.

The gate checks whether claims, evidence, uncertainties, questions, and next
steps are explicit. It does not assess scientific truth or presentation style.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_FIELDS = ("meeting_id", "research_question", "claims", "discussion_questions", "next_steps")


def _is_nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_brief(brief: object) -> list[str]:
    """Return every actionable issue in a meeting brief."""
    if not isinstance(brief, dict):
        return ["Brief must be a JSON object."]

    issues: list[str] = []
    for field in REQUIRED_FIELDS:
        if not brief.get(field):
            issues.append(f"Missing required field: {field}")

    claims = brief.get("claims", [])
    if not isinstance(claims, list) or not claims:
        issues.append("claims must be a non-empty list")
    else:
        for index, claim in enumerate(claims, start=1):
            prefix = f"claims[{index}]"
            if not isinstance(claim, dict):
                issues.append(f"{prefix} must be an object")
                continue
            if not _is_nonempty_text(claim.get("statement")):
                issues.append(f"{prefix}.statement is required")
            evidence = claim.get("evidence")
            if not isinstance(evidence, list) or not any(_is_nonempty_text(item) for item in evidence):
                issues.append(f"{prefix}.evidence must contain at least one verifiable source or result")
            if not _is_nonempty_text(claim.get("certainty")):
                issues.append(f"{prefix}.certainty is required (for example: confirmed, probable, unknown)")

    questions = brief.get("discussion_questions", [])
    if not isinstance(questions, list) or len([item for item in questions if _is_nonempty_text(item)]) < 2:
        issues.append("discussion_questions must contain at least two concrete questions")

    next_steps = brief.get("next_steps", [])
    if not isinstance(next_steps, list) or not next_steps:
        issues.append("next_steps must be a non-empty list")
    else:
        for index, step in enumerate(next_steps, start=1):
            prefix = f"next_steps[{index}]"
            if not isinstance(step, dict):
                issues.append(f"{prefix} must be an object")
                continue
            if not _is_nonempty_text(step.get("action")):
                issues.append(f"{prefix}.action is required")
            if not _is_nonempty_text(step.get("success_criterion")):
                issues.append(f"{prefix}.success_criterion is required")

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brief", type=Path, required=True, help="Meeting brief JSON file")
    args = parser.parse_args(argv)
    try:
        brief = json.loads(args.brief.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL: unable to read brief: {error}")
        return 2

    issues = validate_brief(brief)
    if issues:
        print("FAIL")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("PASS: meeting brief has claims, evidence, questions, and testable next steps.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
