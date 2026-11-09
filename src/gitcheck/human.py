"""大小格式化与解析。"""

from __future__ import annotations

import re

_UNITS = ("B", "KiB", "MiB", "GiB", "TiB")
_SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)([BKMGT]?)I?B?", re.IGNORECASE)
_MULTIPLIERS = {"B": 1, "K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}


def human_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    value = float(size)
    unit = 0
    while value >= 1024 and unit < len(_UNITS) - 1:
        value /= 1024
        unit += 1
    return f"{value:.1f} {_UNITS[unit]}"


def parse_size(raw: str) -> int:
    match = _SIZE_RE.fullmatch(raw.strip())
    if not match:
        raise ValueError(f"无法解析大小：{raw!r}")
    value = float(match.group(1))
    unit = (match.group(2) or "B").upper()
    return int(value * _MULTIPLIERS[unit])
