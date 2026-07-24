from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "project_quality_gate.py"
SPEC = importlib.util.spec_from_file_location("project_quality_gate", MODULE_PATH)
assert SPEC and SPEC.loader
QUALITY_GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(QUALITY_GATE)


class ProjectQualityGateTests(unittest.TestCase):
    def test_complete_project_passes_all_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for filename in ("README.md", "LICENSE", "requirements.txt", ".gitignore"):
                (root / filename).write_text("placeholder", encoding="utf-8")
            for directory in ("src", "tests", "configs"):
                (root / directory).mkdir()

            checks = QUALITY_GATE.inspect_project(root)

        self.assertTrue(all(checks.values()))

    def test_missing_project_contract_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checks = QUALITY_GATE.inspect_project(Path(temporary))

        self.assertFalse(any(checks.values()))

    def test_existing_sci_template_layout_is_recognized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for filename in ("LICENSE", "requirements.txt", ".gitignore"):
                (root / filename).write_text("placeholder", encoding="utf-8")
            for directory in (
                "00_项目说明",
                "01_数据",
                "02_代码/tests",
                "03_图表",
                "06_审计与留痕",
                "configs",
            ):
                (root / directory).mkdir(parents=True, exist_ok=True)
            (root / "00_项目说明" / "README.md").write_text("placeholder", encoding="utf-8")

            checks = QUALITY_GATE.inspect_project(root)

        self.assertTrue(all(checks.values()))


if __name__ == "__main__":
    unittest.main()
