import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "figure_release_gate.py"
SPEC = importlib.util.spec_from_file_location("figure_release_gate", MODULE_PATH)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gate)


class FigureReleaseGateTests(unittest.TestCase):
    def valid_manifest(self) -> dict:
        return {
            "figure_id": "fig-01",
            "title": "Example",
            "intended_use": "journal",
            "source_data": {
                "path": "data/processed.csv",
                "checksum": "sha256:abc",
                "access": "public",
            },
            "render": {"script": "scripts/make_figure.py", "software": "QGIS 3.x"},
            "outputs": [{"file": "figure-01.png", "format": "png", "dpi": 300}],
            "geospatial": {"crs": "EPSG:4326"},
        }

    def test_valid_portable_manifest_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            figure_dir = Path(directory)
            (figure_dir / "figure-01.png").write_bytes(b"sample")
            self.assertEqual(gate.validate_manifest(self.valid_manifest(), figure_dir), [])

    def test_local_path_and_low_dpi_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = self.valid_manifest()
            manifest["source_data"]["path"] = "C:" + r"\Users\person\data.csv"
            manifest["outputs"][0]["dpi"] = 150
            issues = gate.validate_manifest(manifest, Path(directory))
            self.assertTrue(any("relative path" in issue for issue in issues))
            self.assertTrue(any("dpi" in issue for issue in issues))

    def test_format_mismatch_and_undisclosed_restricted_data_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            figure_dir = Path(directory)
            (figure_dir / "figure-01.png").write_bytes(b"sample")
            manifest = self.valid_manifest()
            manifest["outputs"][0]["format"] = "pdf"
            manifest["source_data"]["access"] = "restricted"
            issues = gate.validate_manifest(manifest, figure_dir)
            self.assertTrue(any("extension must match" in issue for issue in issues))
            self.assertTrue(any("public_description" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
