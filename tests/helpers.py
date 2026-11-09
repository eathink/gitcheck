import subprocess
from pathlib import Path


def git(root, *args, env=None):
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


def init_repo(root: Path) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.com")
    git(root, "commit", "--allow-empty", "-q", "-m", "init")
    return root


def stage_file(root: Path, name: str, content: bytes | str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    git(root, "add", name)
