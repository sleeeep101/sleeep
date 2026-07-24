import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "run_synthetic_example.py"
SPEC = importlib.util.spec_from_file_location("run_synthetic_example", MODULE_PATH)
example = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(example)


class SyntheticExampleTests(unittest.TestCase):
    def test_calculate_risk_is_bounded(self) -> None:
        config = {"slope_reference_degrees": 45, "weights": {"slope": 0.5, "soil_erodibility": 0.3, "vegetation_loss": 0.2}}
        score = example.calculate_risk({"slope_degrees": "90", "soil_erodibility": "2", "vegetation_cover": "-1"}, config)
        self.assertEqual(score, 100.0)

    def test_run_writes_one_output_per_input_row(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.csv"
            config_path = root / "config.json"
            output = root / "output.csv"
            source.write_text("site_id,slope_degrees,soil_erodibility,vegetation_cover\nA,10,0.2,0.8\n", encoding="utf-8")
            config_path.write_text(json.dumps({"slope_reference_degrees": 45, "weights": {"slope": 0.5, "soil_erodibility": 0.3, "vegetation_loss": 0.2}}), encoding="utf-8")

            self.assertEqual(example.run(source, config_path, output), 1)
            self.assertIn("synthetic_risk_score", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
