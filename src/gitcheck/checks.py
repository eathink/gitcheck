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


def sort_findings(findings: list[Finding]) -> list[Finding]:
    findings.sort(
        key=lambda item: (
            0 if item.severity == HIGH else 1,
            item.location,
        )
    )
    return findings


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

    return sort_findings(findings)


def _message_entries(message: str) -> list[tuple[int, str]]:
    """去掉注释行与尾部空行，保留原始行号。"""
    entries = [
        (number, line.rstrip())
        for number, line in enumerate(message.splitlines(), 1)
        if not line.lstrip().startswith("#")
    ]
    while entries and not entries[-1][1].strip():
        entries.pop()
    return entries


def check_commit_message(message: str, config: Config) -> list[Finding]:
    """检查 commit-msg 钩子收到的提交信息。

    默认只做结构检查；配置了 commit_message_pattern 才强制标题格式，
    避免对没用 Conventional Commits 的仓库强加规则。
    """
    entries = _message_entries(message)
    if not entries or not entries[0][1].strip():
        return [Finding("commit_message", HIGH, "commit-msg", "提交信息为空")]

    findings: list[Finding] = []
    subject_line, subject = entries[0]
    location = f"commit-msg:{subject_line}"

    if len(subject) > config.max_subject_length:
        findings.append(
            Finding(
                "commit_subject_length",
                MEDIUM,
                location,
                f"标题 {len(subject)} 字符，超过上限 {config.max_subject_length}",
            )
        )

    if len(entries) > 1 and entries[1][1].strip():
        findings.append(
            Finding(
                "commit_body_separator",
                MEDIUM,
                f"commit-msg:{entries[1][0]}",
                "标题与正文之间需要空行",
            )
        )

    if config.commit_message_pattern and not re.fullmatch(
        config.commit_message_pattern, subject
    ):
        findings.append(
            Finding(
                "commit_subject_pattern",
                MEDIUM,
                location,
                "标题不符合 commit_message_pattern",
            )
        )

    return sort_findings(findings)
