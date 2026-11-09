import json
import tempfile
import unittest
from pathlib import Path

from gitcheck.config import Config, ConfigError, load_config


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def write(self, data) -> str:
        path = self.root / ".gitcheck.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return str(path)

    def test_defaults(self):
        config = load_config()

        self.assertEqual(config.max_file_size, 1024 * 1024)
        self.assertIsNone(config.branch_pattern)

    def test_custom_values(self):
        config = load_config(
            self.write({"max_file_size": 2048, "branch_pattern": "^feat/"})
        )

        self.assertEqual(config.max_file_size, 2048)
        self.assertEqual(config.branch_pattern, "^feat/")

    def test_unknown_key_rejected(self):
        with self.assertRaises(ConfigError):
            load_config(self.write({"max_filesize": 1}))

    def test_invalid_size_rejected(self):
        for value in (0, -1, "10", True):
            with self.subTest(value=value):
                with self.assertRaises(ConfigError):
                    load_config(self.write({"max_file_size": value}))

    def test_invalid_regex_rejected(self):
        with self.assertRaises(ConfigError):
            load_config(self.write({"branch_pattern": "("}))

    def test_missing_file_rejected(self):
        with self.assertRaises(ConfigError):
            load_config(str(self.root / "missing.json"))


if __name__ == "__main__":
    unittest.main()
