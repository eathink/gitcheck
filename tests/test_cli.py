import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from gitcheck.cli import main
from helpers import init_repo, stage_file


class CliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        init_repo(self.root)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_clean_returns_zero(self):
        stage_file(self.root, "a.txt", "hello\n")

        code, out, _ = self.run_cli(str(self.root))

        self.assertEqual(code, 0)
        self.assertIn("未发现问题", out)

    def test_findings_return_one_as_json(self):
        stage_file(
            self.root,
            "conflict.txt",
            "<<<<<<< HEAD\nours\n=======\ntheirs\n>>>>>>> branch\n",
        )

        code, out, _ = self.run_cli(str(self.root), "--format", "json")

        payload = json.loads(out)
        self.assertEqual(code, 1)
        self.assertTrue(
            any(item["kind"] == "conflict_marker" for item in payload["findings"])
        )

    def test_config_file_is_discovered(self):
        (self.root / ".gitcheck.json").write_text(
            '{"branch_pattern": "^feat/"}', encoding="utf-8"
        )
        stage_file(self.root, "a.txt", "hello\n")

        code, out, _ = self.run_cli(str(self.root))

        self.assertEqual(code, 1)
        self.assertIn("分支名", out)

    def test_cli_overrides_config(self):
        (self.root / ".gitcheck.json").write_text(
            '{"branch_pattern": "^feat/"}', encoding="utf-8"
        )
        stage_file(self.root, "a.txt", "hello\n")

        code, _, _ = self.run_cli(
            str(self.root), "--branch-pattern", "^main$"
        )

        self.assertEqual(code, 0)

    def test_max_size_override(self):
        stage_file(self.root, "big.bin", b"x" * 2048)

        code, out, _ = self.run_cli(str(self.root), "--max-size", "1K")

        self.assertEqual(code, 1)
        self.assertIn("超过上限", out)

    def test_not_a_repo_returns_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = self.run_cli(tmp)

        self.assertEqual(code, 2)
        self.assertIn("gitcheck:", err)

    def message_file(self, text: str) -> str:
        path = self.root / "COMMIT_EDITMSG"
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_commit_msg_clean(self):
        stage_file(self.root, "a.txt", "hello\n")
        message = self.message_file("feat: add greeting\n")

        code, out, _ = self.run_cli(str(self.root), "--commit-msg", message)

        self.assertEqual(code, 0)
        self.assertIn("未发现问题", out)

    def test_commit_msg_pattern_failure(self):
        (self.root / ".gitcheck.json").write_text(
            '{"commit_message_pattern": "^feat: .+"}', encoding="utf-8"
        )
        stage_file(self.root, "a.txt", "hello\n")
        message = self.message_file("update stuff\n")

        code, out, _ = self.run_cli(str(self.root), "--commit-msg", message)

        self.assertEqual(code, 1)
        self.assertIn("commit_message_pattern", out)

    def test_commit_msg_finding_in_json(self):
        stage_file(self.root, "a.txt", "hello\n")
        message = self.message_file("")

        code, out, _ = self.run_cli(
            str(self.root), "--commit-msg", message, "--format", "json"
        )

        payload = json.loads(out)
        self.assertEqual(code, 1)
        self.assertEqual(payload["findings"][0]["kind"], "commit_message")

    def test_commit_msg_and_staged_findings_combine(self):
        stage_file(
            self.root,
            "conflict.txt",
            "<<<<<<< HEAD\nours\n=======\ntheirs\n>>>>>>> branch\n",
        )
        message = self.message_file("")

        code, out, _ = self.run_cli(
            str(self.root), "--commit-msg", message, "--format", "json"
        )

        kinds = {item["kind"] for item in json.loads(out)["findings"]}
        self.assertEqual(code, 1)
        self.assertEqual(kinds, {"conflict_marker", "commit_message"})

    def test_commit_msg_missing_file_returns_two(self):
        stage_file(self.root, "a.txt", "hello\n")

        code, _, err = self.run_cli(
            str(self.root), "--commit-msg", str(self.root / "missing-msg")
        )

        self.assertEqual(code, 2)
        self.assertIn("无法读取提交信息", err)


if __name__ == "__main__":
    unittest.main()
