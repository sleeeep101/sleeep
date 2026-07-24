#!/usr/bin/env python3
"""Build a new public-release copy without modifying the local workflow."""

from __future__ import annotations

import argparse
import os
import re
import shutil
from pathlib import Path
from typing import Iterable


DEFAULT_SOURCE = Path(__file__).resolve().parent.parent
EXCLUDED_DIR_NAMES = {
    ".claude", ".git", ".learnings", "__pycache__", "data", "logs",
    "90_待人工确认", "98_迁移记录",
}
EXCLUDED_PREFIXES = (
    "01_读_论文阅读与复盘/01_每日论文",
    "01_读_论文阅读与复盘/02_论文阅读库",
    "01_读_论文阅读与复盘/04_长期知识库",
    "01_读_论文阅读与复盘/05_阅读提示词",
    "02_作图与分析/01_作图/qgis_automation_module/task_results",
    "02_作图与分析/01_作图/qgis_automation_module/08_deep_evaluation/computer_use_failure_archive",
    "03_写_论文写作/03_段落素材/grammar_reports",
    "04_SCI三区论文项目/202606_RUSLE_川东北紫色土",
    "04_SCI三区论文项目/_tmp_day2_arcpy",
)
EXCLUDED_FILES = {
    "knowledge_graph/.kg_hash_cache.json", "knowledge_graph/graph.html",
    "knowledge_graph/kg_canvas.json", "knowledge_graph/kg_data.json",
    "knowledge_graph/kg_data_history.json",
    "03_写_论文写作/03_段落素材/full_system_test_report_2026-06-04.md",
    "03_写_论文写作/config/source_files_used.md",
    "03_写_论文写作/config/source_project_index.md",
}
TEXT_SUFFIXES = {".bat", ".cfg", ".csv", ".json", ".md", ".py", ".ps1", ".toml", ".txt", ".yaml", ".yml"}
SENSITIVE_PATH_PATTERNS = (
    re.compile(r"(?i)(?<![A-Za-z])[A-Z]:[\\/][^\s`'\"<>|]+"),
    re.compile(r"(?i)(?<![A-Za-z0-9_])/(?:home|users)/[^\s`'\"<>]+"),
)


class ReleaseSafetyError(RuntimeError):
    """Raised when a candidate public release contains local-path evidence."""


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_excluded(relative_path: str) -> bool:
    if relative_path in EXCLUDED_FILES:
        return True
    return any(relative_path == prefix or relative_path.startswith(f"{prefix}/") for prefix in EXCLUDED_PREFIXES)


def _iter_candidates(source: Path) -> Iterable[Path]:
    for current, directories, files in os.walk(source, topdown=True):
        current_path = Path(current)
        directories[:] = [
            name for name in directories
            if name not in EXCLUDED_DIR_NAMES
            and not _is_excluded(_relative(current_path / name, source))
        ]
        for file_name in files:
            candidate = current_path / file_name
            if not _is_excluded(_relative(candidate, source)):
                yield candidate


def _path_violations(path: Path, relative_path: str) -> list[str]:
    if path.suffix.casefold() not in TEXT_SUFFIXES:
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as error:
        return [f"{relative_path}: cannot read text safely ({error})"]
    return [
        f"{relative_path}:{line_number}"
        for line_number, line in enumerate(lines, start=1)
        if any(pattern.search(line) for pattern in SENSITIVE_PATH_PATTERNS)
    ]


def _redact_local_paths(text: str) -> tuple[str, int]:
    """Return public-copy text with local absolute paths replaced by a marker."""
    total = 0
    for pattern in SENSITIVE_PATH_PATTERNS:
        text, count = pattern.subn("<LOCAL_PATH>", text)
        total += count
    return text, total


def build_release(
    source: Path,
    destination: Path,
    *,
    dry_run: bool = False,
    redact_local_paths: bool = False,
) -> dict[str, int]:
    """Copy a screened public release to a new destination without altering source."""
    source = source.resolve()
    destination = destination.resolve()
    if not source.is_dir():
        raise NotADirectoryError(f"source directory does not exist: {source}")
    if destination.exists():
        raise FileExistsError(f"destination already exists; refusing to overwrite: {destination}")
    if destination == source or source in destination.parents:
        raise ValueError("destination must be outside the source directory")

    candidates = list(_iter_candidates(source))
    violations = [
        violation for candidate in candidates
        for violation in _path_violations(candidate, _relative(candidate, source))
    ]
    if violations and not redact_local_paths:
        preview = "\n- ".join(violations[:20])
        more = "" if len(violations) <= 20 else f"\n... plus {len(violations) - 20} more"
        raise ReleaseSafetyError("local absolute paths found in candidate release files:\n- " + preview + more)

    redacted_paths = 0
    if not dry_run:
        for candidate in candidates:
            target = destination / candidate.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(candidate, target)
            if candidate.suffix.casefold() in TEXT_SUFFIXES:
                text = candidate.read_text(encoding="utf-8", errors="replace")
                redacted, count = _redact_local_paths(text)
                if count:
                    target.write_text(redacted, encoding="utf-8")
                    redacted_paths += count
    return {
        "copied_files": len(candidates),
        "excluded_directories": len(EXCLUDED_DIR_NAMES),
        "redacted_paths": redacted_paths,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Local workflow source; any location is allowed.")
    parser.add_argument("--destination", type=Path, required=True, help="New, non-existent directory for the public copy.")
    parser.add_argument("--dry-run", action="store_true", help="Screen only; do not create a release directory.")
    parser.add_argument("--redact-local-paths", action="store_true", help="Replace detected absolute local paths in the release copy only.")
    args = parser.parse_args(argv)
    try:
        summary = build_release(
            args.source,
            args.destination,
            dry_run=args.dry_run,
            redact_local_paths=args.redact_local_paths,
        )
    except (OSError, ReleaseSafetyError, ValueError) as error:
        print(f"FAIL: {error}")
        return 1
    action = "Screen passed" if args.dry_run else "Release created"
    print(
        f"PASS: {action}; {summary['copied_files']} files eligible for public release; "
        f"{summary['redacted_paths']} local paths redacted."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
