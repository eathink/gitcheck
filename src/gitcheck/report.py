"""渲染检查结果。"""

from __future__ import annotations

import json

from .checks import HIGH, Finding
from .repo import Repo

_SEVERITY_LABEL = {HIGH: "高", "medium": "中"}


def render_text(repo: Repo, findings: list[Finding]) -> str:
    branch = repo.branch or "detached HEAD"
    lines = [
        f"检查 {repo.root}（分支 {branch}，暂存 {len(repo.staged)} 个文件）",
        "",
    ]
    if not findings:
        lines.append("✓ 未发现问题。")
        return "\n".join(lines)

    for finding in findings:
        label = _SEVERITY_LABEL.get(finding.severity, finding.severity)
        lines.append(f"[{label}] {finding.location}  {finding.message}")
    lines.append("")
    lines.append(f"{len(findings)} 个问题")
    return "\n".join(lines)


def render_json(repo: Repo, findings: list[Finding]) -> str:
    payload = {
        "root": str(repo.root),
        "branch": repo.branch,
        "staged_files": len(repo.staged),
        "findings": [
            {
                "kind": finding.kind,
                "severity": finding.severity,
                "location": finding.location,
                "message": finding.message,
            }
            for finding in findings
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
