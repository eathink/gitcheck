"""执行检查项。"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .config import Config
from .human import human_size
from .repo import Repo, blob_sizes, conflict_markers

HIGH = "high"
MEDIUM = "medium"


@dataclass(frozen=True)
class Finding:
    kind: str
    severity: str
    location: str
    message: str


def check(repo: Repo, config: Config) -> list[Finding]:
    findings: list[Finding] = []

    for path, line in conflict_markers(repo.root):
        findings.append(
            Finding("conflict_marker", HIGH, f"{path}:{line}", "存在冲突标记")
        )

    regular = [file for file in repo.staged if file.mode.startswith("100")]
    sizes = blob_sizes(repo.root, [file.sha for file in regular])
    for file in regular:
        size = sizes.get(file.sha)
        if size is not None and size > config.max_file_size:
            findings.append(
                Finding(
                    "large_file",
                    MEDIUM,
                    file.path,
                    f"{human_size(size)}，超过上限 {human_size(config.max_file_size)}",
                )
            )

    if config.branch_pattern and repo.branch:
        if not re.fullmatch(config.branch_pattern, repo.branch):
            findings.append(
                Finding(
                    "branch_name",
                    MEDIUM,
                    repo.branch,
                    "分支名不符合命名规则",
                )
            )

    findings.sort(
        key=lambda item: (
            0 if item.severity == HIGH else 1,
            item.location,
        )
    )
    return findings
