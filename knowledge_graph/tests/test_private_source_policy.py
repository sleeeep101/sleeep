import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "graph" / "builder.py"


class PrivateSourcePolicyTests(unittest.TestCase):
    def test_builder_defaults_to_excluding_private_sources(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        signature = "def __init__(self, kg_file: str = KG_DATA_FILE, *, include_private_sources: bool = False):"
        self.assertIn(signature, source)
        self.assertIn("if not self.include_private_sources:", source)
        self.assertIn("Private sources skipped", source)
        self.assertIn("if os.path.isdir(pb_root) and self.include_private_sources:", source)
        self.assertLess(
            source.index("rl_ext = ReadingListExtractor"),
            source.index("if not self.include_private_sources:"),
        )
        self.assertLess(
            source.index("if not self.include_private_sources:"),
            source.index("dn_ext = DesktopNotesExtractor"),
        )

    def test_cli_requires_an_explicit_private_source_flag(self) -> None:
        cli_path = MODULE_PATH.parent.parent / "cli.py"
        source = cli_path.read_text(encoding="utf-8")
        self.assertEqual(source.count('"--include-private-sources"'), 2)
        self.assertIn("include_private_sources=args.include_private_sources", source)


if __name__ == "__main__":
    unittest.main()
