"""Command-line interface for repo-health-agent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .analyzer import analyze_repository


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-health",
        description="Measure the health of a local Git repository.",
    )
    parser.add_argument("--path", default=".", help="Path to the Git repository (default: current directory).")
    parser.add_argument("--format", choices=("text", "json"), default="text", dest="output_format")
    return parser


def _render_text(report: dict[str, Any]) -> str:
    lines = [
        f"Repository: {report['repository']}",
        f"Health: {report['status']} ({report['percentage']}%, {report['score']}/{report['max_score']})",
        "",
        "Checks:",
    ]
    for check in report["checks"]:
        lines.append(f"  [{check['status'].upper():4}] {check['name']}: {check['detail']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = analyze_repository(Path(args.path))
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.output_format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_text(report))
    return 0
