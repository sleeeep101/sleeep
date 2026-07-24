#!/usr/bin/env python3
"""Check whether a research project has the minimum reproducibility boundary.

Inspired by project-structure practices in Cookiecutter Data Science (MIT).
This tool reads only the project path explicitly supplied by the user and writes
nothing. It is not a substitute for scientific validation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DOCUMENTATION = ("README.md", "00_项目说明/README.md")
ENVIRONMENT_FILES = ("requirements.txt", "pyproject.toml", "environment.yml")
CODE_DIRECTORIES = ("src", "scripts", "02_代码")
TEST_DIRECTORIES = ("tests", "02_代码/tests")
CONFIG_DIRECTORIES = ("configs", "config")
DATA_BOUNDARY_FILES = (".gitignore", "DATA_ACCESS.md", "data/README.md")


def exists_any(root: Path, candidates: tuple[str, ...]) -> bool:
    return any((root / item).exists() for item in candidates)


def inspect_project(root: Path) -> dict[str, bool]:
    """Return deterministic checks for a user-selected project directory."""
    return {
        "documentation": exists_any(root, DOCUMENTATION),
        "license": (root / "LICENSE").exists() or (root / "LICENSE.md").exists(),
        "environment": exists_any(root, ENVIRONMENT_FILES),
        "code": exists_any(root, CODE_DIRECTORIES),
        "tests": exists_any(root, TEST_DIRECTORIES),
        "data_boundary": exists_any(root, DATA_BOUNDARY_FILES),
        "configuration": exists_any(root, CONFIG_DIRECTORIES),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check the reproducibility boundary of a research project."
    )
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    args = parser.parse_args()

    root = args.project.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"Project directory does not exist: {root}")

    checks = inspect_project(root)
    passed = sum(checks.values())
    if args.json:
        print(json.dumps({"project": str(root), "checks": checks, "passed": passed}, ensure_ascii=False))
    else:
        print(f"Project: {root}")
        for name, value in checks.items():
            print(f"{'PASS' if value else 'MISSING'}  {name}")
        print(f"Score: {passed}/{len(checks)}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
