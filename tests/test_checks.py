import subprocess
import tempfile
import unittest
from pathlib import Path

from gitcheck.checks import check, check_commit_message
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


class CommitMessageTests(unittest.TestCase):
    PATTERN = r"^(feat|fix|docs|chore)(\([^)]+\))?: .+"

    def test_clean_message_with_pattern(self):
        findings = check_commit_message(
            "feat(cli): add commit-msg check\n\nBody text.\n",
            Config(commit_message_pattern=self.PATTERN),
        )
        self.assertEqual(findings, [])

    def test_defaults_do_not_force_conventional_commits(self):
        findings = check_commit_message("修一下文档", Config())
        self.assertEqual(findings, [])

    def test_empty_message(self):
        for message in ("", "\n\n", "# comment only\n"):
            with self.subTest(message=message):
                findings = check_commit_message(message, Config())
                self.assertEqual(len(findings), 1)
                self.assertEqual(findings[0].kind, "commit_message")
                self.assertEqual(findings[0].severity, "high")

    def test_subject_too_long(self):
        findings = check_commit_message(
            "feat: " + "x" * 20, Config(max_subject_length=20)
        )
        self.assertEqual([item.kind for item in findings], ["commit_subject_length"])
        self.assertIn("超过上限 20", findings[0].message)

    def test_subject_at_limit_passes(self):
        subject = "x" * 20
        self.assertEqual(
            check_commit_message(subject, Config(max_subject_length=20)), []
        )

    def test_body_needs_blank_line(self):
        findings = check_commit_message("feat: add\nbody on next line", Config())
        self.assertEqual([item.kind for item in findings], ["commit_body_separator"])
        self.assertEqual(findings[0].location, "commit-msg:2")

    def test_body_with_blank_line_passes(self):
        self.assertEqual(
            check_commit_message("feat: add\n\nbody on next line", Config()), []
        )

    def test_pattern_mismatch(self):
        findings = check_commit_message(
            "update stuff", Config(commit_message_pattern=self.PATTERN)
        )
        self.assertEqual([item.kind for item in findings], ["commit_subject_pattern"])

    def test_comment_lines_ignored(self):
        message = "feat: add\n\n# Please enter the commit message\n# On branch main\n"
        self.assertEqual(check_commit_message(message, Config()), [])

    def test_reports_original_line_number(self):
        findings = check_commit_message(
            "# leading comment\nupdate stuff", Config(commit_message_pattern=self.PATTERN)
        )
        self.assertEqual(findings[0].location, "commit-msg:2")


if __name__ == "__main__":
    unittest.main()
