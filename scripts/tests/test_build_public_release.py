import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "build_public_release.py"
SPEC = importlib.util.spec_from_file_location("build_public_release", MODULE_PATH)
builder = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(builder)


def local_path_fixture() -> str:
    return "Local location: " + "C:" + r"\Users\Example\notes"


class PublicReleaseBuilderTests(unittest.TestCase):
    def test_safe_files_copy_and_private_directories_are_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            destination = Path(directory) / "release"
            (source / "module").mkdir(parents=True)
            (source / "data").mkdir()
            knowledge_base = source / "01_读_论文阅读与复盘" / "04_长期知识库"
            knowledge_base.mkdir(parents=True)
            (source / "module" / "README.md").write_text("portable guide", encoding="utf-8")
            (source / "data" / "notes.md").write_text("local corpus", encoding="utf-8")
            (knowledge_base / "notes.md").write_text("local knowledge base", encoding="utf-8")

            summary = builder.build_release(source, destination)

            self.assertEqual(summary["copied_files"], 1)
            self.assertTrue((destination / "module" / "README.md").is_file())
            self.assertFalse((destination / "data").exists())
            self.assertFalse((destination / "01_读_论文阅读与复盘" / "04_长期知识库").exists())

    def test_local_absolute_path_blocks_the_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            destination = Path(directory) / "release"
            source.mkdir()
            (source / "guide.md").write_text(local_path_fixture(), encoding="utf-8")

            with self.assertRaises(builder.ReleaseSafetyError):
                builder.build_release(source, destination)
            self.assertFalse(destination.exists())

    def test_explicit_redaction_mode_replaces_local_paths_only_in_the_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            destination = Path(directory) / "release"
            source.mkdir()
            original = local_path_fixture()
            (source / "guide.md").write_text(original, encoding="utf-8")

            summary = builder.build_release(source, destination, redact_local_paths=True)

            released = (destination / "guide.md").read_text(encoding="utf-8")
            self.assertEqual(summary["redacted_paths"], 1)
            self.assertIn("<LOCAL_PATH>", released)
            self.assertNotIn("C:" + r"\Users", released)
            self.assertEqual((source / "guide.md").read_text(encoding="utf-8"), original)

    def test_existing_destination_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            destination = Path(directory) / "release"
            source.mkdir()
            destination.mkdir()

            with self.assertRaises(FileExistsError):
                builder.build_release(source, destination)


if __name__ == "__main__":
    unittest.main()
