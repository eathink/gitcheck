"""命令行入口。"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .checks import check
from .config import Config, ConfigError, load_config, validate_pattern
from .human import parse_size
from .repo import RepoError, discover
from .report import render_json, render_text


def _size(raw: str) -> int:
    try:
        return parse_size(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gitcheck",
        description="提交前检查暂存区：冲突标记、超大文件、分支命名。",
    )
    parser.add_argument("path", nargs="?", default=".", help="仓库路径（默认当前目录）")
    parser.add_argument("--config", metavar="FILE", help="配置文件（默认读取仓库根的 .gitcheck.json）")
    parser.add_argument("--max-size", type=_size, metavar="SIZE", help="单文件大小上限，覆盖配置")
    parser.add_argument("--branch-pattern", metavar="REGEX", help="分支名正则，覆盖配置")
    parser.add_argument(
        "-f", "--format", choices=("text", "json"), default="text", help="输出格式"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        repo = discover(args.path)
    except RepoError as exc:
        print(f"gitcheck: {exc}", file=sys.stderr)
        return 2

    config_path = args.config
    if config_path is None and (repo.root / ".gitcheck.json").is_file():
        config_path = str(repo.root / ".gitcheck.json")

    try:
        config = load_config(config_path)
        if args.max_size is not None:
            config = Config(args.max_size, config.branch_pattern)
        if args.branch_pattern is not None:
            config = Config(
                config.max_file_size, validate_pattern(args.branch_pattern)
            )
    except ConfigError as exc:
        print(f"gitcheck: {exc}", file=sys.stderr)
        return 2

    findings = check(repo, config)
    if args.format == "json":
        print(render_json(repo, findings))
    else:
        print(render_text(repo, findings))

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
