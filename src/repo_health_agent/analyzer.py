"""Deterministic health checks for local Git repositories."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import subprocess
from typing import Any


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    points: int
    max_points: int
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _exists(repo: Path, names: tuple[str, ...]) -> bool:
    return any((repo / name).exists() for name in names)


def _activity_check(repo: Path) -> CheckResult:
    try:
        timestamp = _git(repo, "log", "-1", "--format=%cI")
        committed = datetime.fromisoformat(timestamp).astimezone(timezone.utc)
    except (subprocess.CalledProcessError, ValueError):
        return CheckResult("recent_commit", "fail", 0, 15, "No readable commit history was found.")

    age_days = max((datetime.now(timezone.utc) - committed).days, 0)
    if age_days <= 30:
        return CheckResult("recent_commit", "pass", 15, 15, f"Latest commit is {age_days} day(s) old.")
    if age_days <= 90:
        return CheckResult("recent_commit", "warn", 8, 15, f"Latest commit is {age_days} day(s) old.")
    return CheckResult("recent_commit", "fail", 0, 15, f"Latest commit is {age_days} day(s) old.")


def _working_tree_check(repo: Path) -> CheckResult:
    try:
        changes = _git(repo, "status", "--porcelain")
    except subprocess.CalledProcessError:
        return CheckResult("working_tree", "fail", 0, 15, "Git status could not be read.")
    if changes:
        count = len(changes.splitlines())
        return CheckResult("working_tree", "warn", 7, 15, f"{count} uncommitted change(s) detected.")
    return CheckResult("working_tree", "pass", 15, 15, "Working tree is clean.")


def _branch_check(repo: Path) -> CheckResult:
    try:
        branch = _git(repo, "branch", "--show-current") or "detached HEAD"
    except subprocess.CalledProcessError:
        return CheckResult("branch", "fail", 0, 10, "The current branch could not be read.")
    if branch in {"main", "master"}:
        return CheckResult("branch", "pass", 10, 10, f"Repository is on {branch}.")
    return CheckResult("branch", "warn", 6, 10, f"Repository is on {branch}.")


def _presence_check(
    repo: Path,
    name: str,
    paths: tuple[str, ...],
    max_points: int,
    detail: str,
) -> CheckResult:
    if _exists(repo, paths):
        return CheckResult(name, "pass", max_points, max_points, detail)
    return CheckResult(name, "warn", 0, max_points, f"Missing expected {name.replace('_', ' ')} metadata.")


def analyze_repository(path: str | Path) -> dict[str, Any]:
    """Analyze *path* and return a JSON-serializable health report."""
    repo = Path(path).expanduser().resolve()
    if not repo.is_dir():
        raise ValueError(f"Repository path does not exist or is not a directory: {repo}")
    try:
        _git(repo, "rev-parse", "--show-toplevel")
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"Not a Git repository: {repo}") from exc

    checks = [
        _branch_check(repo),
        _activity_check(repo),
        _working_tree_check(repo),
        _presence_check(repo, "readme", ("README", "README.md", "README.rst"), 10, "README documentation is present."),
        _presence_check(repo, "license", ("LICENSE", "LICENSE.md", "LICENSE.txt"), 10, "A license file is present."),
        _presence_check(repo, "ci", (".github/workflows", ".gitlab-ci.yml", "azure-pipelines.yml"), 15, "CI configuration is present."),
        _presence_check(repo, "tests", ("tests", "test", "__tests__"), 15, "A conventional test directory is present."),
        _presence_check(
            repo,
            "dependencies",
            ("pyproject.toml", "package.json", "requirements.txt", "go.mod", "Cargo.toml", "pom.xml", "build.gradle"),
            10,
            "Dependency metadata is present.",
        ),
    ]
    score = sum(check.points for check in checks)
    maximum = sum(check.max_points for check in checks)
    percentage = round(score / maximum * 100) if maximum else 0
    status = "healthy" if percentage >= 80 else "needs-attention" if percentage >= 50 else "critical"
    return {
        "repository": str(repo),
        "score": score,
        "max_score": maximum,
        "percentage": percentage,
        "status": status,
        "checks": [check.as_dict() for check in checks],
    }
