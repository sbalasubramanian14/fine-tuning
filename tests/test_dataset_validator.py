"""Exercise data mistakes that would silently harm a character training run."""
import importlib.util
import subprocess
import sys
import shutil
import unittest
import uuid
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validator", ROOT / "scripts/validate_dataset.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class DatasetValidationTests(unittest.TestCase):
    def setUp(self):
        temp_root = (ROOT / '.cache/tests').resolve()
        if not temp_root.is_relative_to(ROOT.resolve()):
            raise RuntimeError('Test temporary directory must be inside the repository')
        temp_root.mkdir(parents=True, exist_ok=True)
        self.root = temp_root / uuid.uuid4().hex
        self.root.mkdir()

    def tearDown(self):
        resolved = self.root.resolve()
        if not resolved.is_relative_to((ROOT / '.cache/tests').resolve()):
            raise RuntimeError('Refusing to remove a path outside test fixtures')
        shutil.rmtree(resolved)

    def make_image(self, folder, stem, color="red", caption="soraskychar, portrait"):
        folder.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (512, 512), color).save(folder / f"{stem}.png")
        if caption is not None:
            (folder / f"{stem}.txt").write_text(caption, encoding="utf-8")

    def test_caption_required(self):
        self.make_image(self.root, "one", caption=None)
        _, errors = validator.inspect(self.root, "soraskychar")
        self.assertTrue(any("missing .txt" in error for error in errors))

    def test_trigger_must_be_first_tag(self):
        self.make_image(self.root, "one", caption="portrait, soraskychar")
        _, errors = validator.inspect(self.root, "soraskychar")
        self.assertTrue(any("must start" in error for error in errors))

    def test_pixel_duplicates_detected(self):
        self.make_image(self.root, "one")
        self.make_image(self.root, "two")
        _, errors = validator.inspect(self.root, "soraskychar")
        self.assertTrue(any("duplicate" in error for error in errors))

    def run_cli(self):
        return subprocess.run([sys.executable, str(ROOT / "scripts/validate_dataset.py"),
                               "--train-dir", str(self.root / "train"),
                               "--validation-dir", str(self.root / "validation"),
                               "--min-train", "1", "--min-validation", "1"],
                              text=True, capture_output=True)

    def test_train_validation_leakage_rejected(self):
        self.make_image(self.root / "train", "one")
        self.make_image(self.root / "validation", "heldout")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Validation leakage", result.stdout)

    def test_distinct_complete_data_accepted(self):
        self.make_image(self.root / "train", "one", color="red")
        self.make_image(self.root / "validation", "heldout", color="blue")
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
