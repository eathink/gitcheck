"""读取 .gitcheck.json 配置。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MAX_FILE_SIZE = 1024 * 1024
_ALLOWED_KEYS = frozenset({"max_file_size", "branch_pattern"})


class ConfigError(ValueError):
    """配置无法解析或校验失败。"""


@dataclass(frozen=True)
class Config:
    max_file_size: int = DEFAULT_MAX_FILE_SIZE
    branch_pattern: str | None = None


def validate_pattern(pattern: str) -> str:
    try:
        re.compile(pattern)
    except re.error as exc:
        raise ConfigError(f"branch_pattern 不是合法正则：{exc}") from exc
    return pattern


def load_config(path: str | Path | None = None) -> Config:
    if path is None:
        return Config()

    config_path = Path(path)
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"无法读取 {path}: {exc.strerror or exc}") from exc

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{config_path}:{exc.lineno}: JSON 解析失败：{exc.msg}") from exc

    if not isinstance(data, dict):
        raise ConfigError(f"{config_path}: 顶层必须是对象")

    unknown = set(data) - _ALLOWED_KEYS
    if unknown:
        raise ConfigError(f"{config_path}: 未知字段 {', '.join(sorted(unknown))}")

    max_file_size = data.get("max_file_size", DEFAULT_MAX_FILE_SIZE)
    if (
        isinstance(max_file_size, bool)
        or not isinstance(max_file_size, int)
        or max_file_size <= 0
    ):
        raise ConfigError(f"{config_path}: max_file_size 必须是正整数")

    pattern = data.get("branch_pattern")
    if pattern is not None:
        if not isinstance(pattern, str) or not pattern:
            raise ConfigError(f"{config_path}: branch_pattern 必须是非空字符串")
        validate_pattern(pattern)

    return Config(max_file_size, pattern)
