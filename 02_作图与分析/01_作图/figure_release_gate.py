"""Validate a portable, reviewable figure manifest before release.

The checker is deliberately dependency-free.  It validates metadata and only
accepts relative paths, preventing accidental publication of local paths.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath


ALLOWED_FORMATS = {"png", "tif", "tiff", "svg", "pdf", "eps"}
ALLOWED_ACCESS = {"public", "restricted", "synthetic"}


def is_portable_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    posix_path = Path(value)
    windows_path = PureWindowsPath(value)
    return not posix_path.is_absolute() and not windows_path.is_absolute() and ".." not in posix_path.parts


def validate_manifest(manifest: dict, figure_dir: Path) -> list[str]:
    """Return all manifest issues.  An empty result means the release gate passes."""
    issues: list[str] = []
    for key in ("figure_id", "title", "intended_use", "source_data", "render", "outputs"):
        if not manifest.get(key):
            issues.append(f"Missing required field: {key}")

    source_data = manifest.get("source_data", {})
    if not isinstance(source_data, dict) or not is_portable_relative_path(source_data.get("path")):
        issues.append("source_data.path must be a non-empty relative path")
    if not isinstance(source_data, dict) or not source_data.get("checksum"):
        issues.append("source_data.checksum is required for data provenance")
    access = source_data.get("access") if isinstance(source_data, dict) else None
    if access not in ALLOWED_ACCESS:
        issues.append(f"source_data.access must be one of {sorted(ALLOWED_ACCESS)}")
    elif access == "restricted" and not source_data.get("public_description"):
        issues.append("restricted source_data requires a non-sensitive public_description")

    render = manifest.get("render", {})
    if not isinstance(render, dict) or not is_portable_relative_path(render.get("script")):
        issues.append("render.script must be a non-empty relative path")
    if not isinstance(render, dict) or not render.get("software"):
        issues.append("render.software is required")

    outputs = manifest.get("outputs", [])
    if not isinstance(outputs, list) or not outputs:
        return issues + ["outputs must be a non-empty list"]
    journal = manifest.get("intended_use") == "journal"
    for index, output in enumerate(outputs, start=1):
        prefix = f"outputs[{index}]"
        if not isinstance(output, dict):
            issues.append(f"{prefix} must be an object")
            continue
        file_name = output.get("file")
        fmt = str(output.get("format", "")).casefold()
        if not is_portable_relative_path(file_name):
            issues.append(f"{prefix}.file must be a non-empty relative path")
        elif not (figure_dir / file_name).is_file():
            issues.append(f"{prefix}.file does not exist under figure_dir: {file_name}")
        if fmt not in ALLOWED_FORMATS:
            issues.append(f"{prefix}.format must be one of {sorted(ALLOWED_FORMATS)}")
        elif isinstance(file_name, str) and Path(file_name).suffix.casefold().lstrip(".") != fmt:
            issues.append(f"{prefix}.file extension must match outputs[{index}].format")
        dpi = output.get("dpi")
        if journal and (not isinstance(dpi, int) or dpi < 300):
            issues.append(f"{prefix}.dpi must be an integer >= 300 for journal figures")

    geospatial = manifest.get("geospatial")
    if geospatial is not None:
        if not isinstance(geospatial, dict) or not geospatial.get("crs"):
            issues.append("geospatial.crs is required when geospatial metadata is supplied")
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--figure-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL: cannot read manifest: {error}")
        return 2
    issues = validate_manifest(manifest, args.figure_dir)
    if issues:
        print("FAIL")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("PASS: figure manifest is portable and complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
