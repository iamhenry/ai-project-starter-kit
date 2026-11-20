#!/usr/bin/env python3
"""Exercise the public checker CLI with small fictional listings."""
import pathlib
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).parent


class MetadataTest(unittest.TestCase):
    def run_check(self, fixture, *extra):
        return subprocess.run(
            [sys.executable, str(HERE / "check_metadata.py"), "--listings",
             str(HERE / "fixtures" / fixture), *extra],
            text=True, capture_output=True, check=False)

    def test_bad(self):
        result = self.run_check("bad.json")
        self.assertEqual(result.returncode, 1)
        for text in ("repeated", "'app'", "exceeds"):
            self.assertIn(text, result.stdout)

    def test_clean(self):
        result = self.run_check("clean.json", "--popularity",
                                str(HERE / "fixtures" / "popularity.json"))
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_one(self):
        self.assertEqual(self.run_check("one.json").returncode, 0)


if __name__ == "__main__":
    unittest.main()
