"""Run a dependency-free synthetic terrain/erosion example.

The input is deliberately synthetic.  The calculated score is a structure
check for the template, not a scientific erosion model or a publishable result.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


REQUIRED_COLUMNS = {"site_id", "slope_degrees", "soil_erodibility", "vegetation_cover"}


def calculate_risk(row: dict[str, str], config: dict) -> float:
    """Return a bounded synthetic risk score from transparent input fields."""
    weights = config["weights"]
    reference_slope = float(config["slope_reference_degrees"])
    slope = min(max(float(row["slope_degrees"]) / reference_slope, 0.0), 1.0)
    soil = min(max(float(row["soil_erodibility"]), 0.0), 1.0)
    vegetation_loss = 1.0 - min(max(float(row["vegetation_cover"]), 0.0), 1.0)
    return round(100 * (weights["slope"] * slope + weights["soil_erodibility"] * soil + weights["vegetation_loss"] * vegetation_loss), 2)


def run(input_path: Path, config_path: Path, output_path: Path) -> int:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    with input_path.open("r", encoding="utf-8", newline="") as input_file:
        rows = list(csv.DictReader(input_file))
    if not rows or not REQUIRED_COLUMNS.issubset(rows[0]):
        raise ValueError(f"Input must contain columns: {sorted(REQUIRED_COLUMNS)}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=["site_id", "synthetic_risk_score"])
        writer.writeheader()
        for row in rows:
            writer.writerow({"site_id": row["site_id"], "synthetic_risk_score": calculate_risk(row, config)})
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    count = run(args.input, args.config, args.output)
    print(f"Processed {count} synthetic records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
