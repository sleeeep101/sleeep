import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "knowledge_graph" / "examples" / "public_graph.json"


class PublicGraphExampleTests(unittest.TestCase):
    def test_example_has_only_synthetic_relative_provenance(self) -> None:
        data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        self.assertEqual(len(data["nodes"]), 3)
        self.assertEqual(len(data["edges"]), 2)
        for node in data["nodes"]:
            self.assertEqual(node["source_type"], "synthetic-example")
            self.assertFalse(Path(node["source_file"]).is_absolute())

    def test_cli_reads_the_public_example_without_default_local_graph(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "knowledge_graph", "stats", "--graph-file", str(EXAMPLE)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("节点总数: 3", result.stdout)
        self.assertIn("边总数:   2", result.stdout)


if __name__ == "__main__":
    unittest.main()
