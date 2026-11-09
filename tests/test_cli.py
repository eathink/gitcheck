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


if __name__ == "__main__":
    unittest.main()
