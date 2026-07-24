"""Batch runner for QGIS Processing algorithms. Chain multiple processes with logging."""
from pathlib import Path
import json
from datetime import datetime
import processing


class BatchRunner:
    """Run a chain of Processing algorithms with logging."""

    def __init__(self, log_path: str = None):
        self.log_path = Path(log_path or f"batch_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        self.steps = []

    def run(self, algorithm: str, params: dict, label: str = "") -> dict:
        """Run one Processing algorithm and log."""
        step = {"label": label or algorithm, "algorithm": algorithm,
                "params": {k: str(v) for k, v in params.items()}, "status": "failed"}
        try:
            result = processing.run(algorithm, params)
            step["status"] = "success"
            step["output"] = {k: str(v) for k, v in result.items()}
            print(f"[OK] {label or algorithm}")
        except Exception as e:
            step["error"] = str(e)
            print(f"[FAIL] {label or algorithm}: {e}")
            raise
        finally:
            self.steps.append(step)
        return result

    def save_log(self):
        """Save batch log to JSON."""
        data = {"timestamp": datetime.now().isoformat(), "total": len(self.steps),
                "success": sum(1 for s in self.steps if s["status"] == "success"),
                "failed": sum(1 for s in self.steps if s["status"] == "failed"),
                "steps": self.steps}
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[OK] Batch log: {self.log_path}")


# Common Processing chains

def dem_to_hillshade_pipeline(dem_path: str, boundary_path: str, output_dir: str):
    """DEM → reproject → clip → hillshade → slope pipeline."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    runner = BatchRunner(str(out / "batch_log.json"))

    reproj = runner.run("gdal:warpreproject", {
        "INPUT": dem_path, "TARGET_CRS": "EPSG:3857",
        "OUTPUT": str(out / "dem_3857.tif")
    }, "Reproject DEM")

    clip = runner.run("gdal:cliprasterbymasklayer", {
        "INPUT": reproj["OUTPUT"], "MASK": boundary_path,
        "OUTPUT": str(out / "dem_clipped.tif")
    }, "Clip DEM")

    hill = runner.run("native:hillshade", {
        "INPUT": clip["OUTPUT"], "AZIMUTH": 315, "V_ANGLE": 45,
        "OUTPUT": str(out / "hillshade.tif")
    }, "Hillshade")

    slope = runner.run("native:slope", {
        "INPUT": clip["OUTPUT"], "OUTPUT": str(out / "slope.tif")
    }, "Slope")

    runner.save_log()
    return {"dem_reprojected": reproj["OUTPUT"], "dem_clipped": clip["OUTPUT"],
            "hillshade": hill["OUTPUT"], "slope_out": slope["OUTPUT"]}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python processing_batch_runner.py dem_pipeline <dem> <boundary> <output_dir>")
        sys.exit(1)
    if sys.argv[1] == "dem_pipeline":
        dem_to_hillshade_pipeline(sys.argv[2], sys.argv[3], sys.argv[4])
