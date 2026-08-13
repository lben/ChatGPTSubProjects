from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import safety_scan  # noqa: E402


class SafetyScanTests(unittest.TestCase):
    def test_safe_text_file_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "README.md"
            path.write_text("No sensitive content.\n", encoding="utf-8")
            self.assertEqual(safety_scan.scan([path], root), [])

    def test_data_extension_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "sample.csv"
            path.write_text("id\n1\n", encoding="utf-8")
            findings = safety_scan.scan([path], root)
            self.assertTrue(any("sensitive file extension" in item for item in findings))

    def test_private_key_marker_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "note.txt"
            marker = "-----BEGIN " + "PRIVATE KEY-----\nabc\n"
            path.write_text(marker, encoding="utf-8")
            findings = safety_scan.scan([path], root)
            self.assertTrue(any("private key" in item for item in findings))

    def test_local_state_path_is_rejected_when_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / ".agent" / "local" / "ACTIVE_TASK.md"
            path.parent.mkdir(parents=True)
            path.write_text("local\n", encoding="utf-8")
            findings = safety_scan.scan([path], root)
            self.assertTrue(any("private local state" in item for item in findings))


if __name__ == "__main__":
    unittest.main()
