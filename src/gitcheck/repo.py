"""读取仓库状态。"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

_MARKER_RE = re.compile(r"^(.*):(\d+): leftover conflict marker$")


class RepoError(ValueError):
    """不是 git 仓库或 git 调用失败。"""


@dataclass(frozen=True)
class StagedFile:
    path: str
    mode: str
    sha: str


@dataclass(frozen=True)
class Repo:
    root: Path
    branch: str | None
    staged: list[StagedFile]


def _git(
    root: str | Path, *args: str, input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        input=input_text,
        check=False,
    )


def discover(path: str | Path = ".") -> Repo:
    target = Path(path).expanduser().resolve()
    top = _git(target, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        raise RepoError(f"不是 git 仓库：{path}")
    root = Path(top.stdout.strip())

    branch_proc = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    branch = branch_proc.stdout.strip() if branch_proc.returncode == 0 else None

    diff = _git(root, "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR")
    staged_paths = {item for item in diff.stdout.split("\0") if item}

    listing = _git(root, "ls-files", "-s", "-z")
    staged: list[StagedFile] = []
    for record in listing.stdout.split("\0"):
        if not record:
            continue
        meta, _, file_path = record.partition("\t")
        parts = meta.split()
        if len(parts) != 3 or file_path not in staged_paths:
            continue
        mode, sha, stage = parts
        if stage != "0":
            continue
        staged.append(StagedFile(file_path, mode, sha))

    return Repo(root, branch, staged)


def conflict_markers(root: Path) -> list[tuple[str, int]]:
    """用 git diff --cached --check 找出暂存内容里的冲突标记。"""
    process = _git(root, "diff", "--cached", "--check")
    markers: list[tuple[str, int]] = []
    for line in process.stdout.splitlines():
        match = _MARKER_RE.match(line)
        if match:
            markers.append((match.group(1), int(match.group(2))))
    return markers


def blob_sizes(root: Path, shas: list[str]) -> dict[str, int]:
    unique = list(dict.fromkeys(shas))
    if not unique:
        return {}

    process = _git(
        root,
        "cat-file",
        "--batch-check=%(objectname) %(objectsize)",
        input_text="\n".join(unique),
    )
    if process.returncode != 0:
        return {}

    sizes: dict[str, int] = {}
    for line in process.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].isdigit():
            sizes[parts[0]] = int(parts[1])
    return sizes
