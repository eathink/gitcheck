import tempfile
import unittest
from pathlib import Path

from gitcheck.repo import RepoError, blob_sizes, conflict_markers, discover
from helpers import init_repo, stage_file


class RepoTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        init_repo(self.root)

    def test_discover_branch_and_staged(self):
        stage_file(self.root, "a.txt", "hello\n")

        repo = discover(self.root)

        self.assertEqual(repo.root, self.root)
        self.assertEqual(repo.branch, "main")
        self.assertEqual([file.path for file in repo.staged], ["a.txt"])
        self.assertTrue(repo.staged[0].mode.startswith("100"))

    def test_committed_file_is_not_staged(self):
        stage_file(self.root, "a.txt", "hello\n")
        import subprocess

        subprocess.run(
            ["git", "-C", str(self.root), "commit", "-q", "-m", "add"],
            check=True,
        )

        repo = discover(self.root)

        self.assertEqual(repo.staged, [])

    def test_not_a_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RepoError):
                discover(tmp)

    def test_conflict_markers(self):
        content = "line1\n<<<<<<< HEAD\nours\n=======\ntheirs\n>>>>>>> branch\n"
        stage_file(self.root, "conflict.txt", content)

        markers = conflict_markers(self.root)

        self.assertTrue(markers)
        self.assertEqual(markers[0][0], "conflict.txt")

    def test_blob_sizes(self):
        stage_file(self.root, "a.txt", "12345")
        repo = discover(self.root)

        sizes = blob_sizes(repo.root, [file.sha for file in repo.staged])

        self.assertEqual(sizes[repo.staged[0].sha], 5)


if __name__ == "__main__":
    unittest.main()
