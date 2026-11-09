import subprocess
import tempfile
import unittest
from pathlib import Path

from gitcheck.checks import check
from gitcheck.config import Config
from gitcheck.repo import discover
from helpers import init_repo, stage_file


class CheckTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        init_repo(self.root)

    def test_clean_stage(self):
        stage_file(self.root, "a.txt", "hello\n")

        findings = check(discover(self.root), Config())

        self.assertEqual(findings, [])

    def test_large_file(self):
        stage_file(self.root, "big.bin", b"x" * 2048)

        findings = check(discover(self.root), Config(max_file_size=1024))

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "large_file")
        self.assertEqual(findings[0].location, "big.bin")

    def test_conflict_marker(self):
        stage_file(
            self.root,
            "conflict.txt",
            "<<<<<<< HEAD\nours\n=======\ntheirs\n>>>>>>> branch\n",
        )

        findings = check(discover(self.root), Config())

        self.assertTrue(any(item.kind == "conflict_marker" for item in findings))
        self.assertTrue(all(item.severity == "high" for item in findings))

    def test_branch_pattern(self):
        stage_file(self.root, "a.txt", "hello\n")

        findings = check(
            discover(self.root), Config(branch_pattern=r"^feat/")
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "branch_name")

    def test_branch_pattern_match(self):
        subprocess.run(
            ["git", "-C", str(self.root), "checkout", "-q", "-b", "feat/demo"],
            check=True,
        )
        stage_file(self.root, "a.txt", "hello\n")

        findings = check(
            discover(self.root), Config(branch_pattern=r"^feat/.*$")
        )

        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
