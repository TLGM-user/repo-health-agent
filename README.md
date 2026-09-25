# repo-health-agent

A dependency-free Python CLI for measuring the health of a local Git repository.

## Requirements

- Python 3.10+
- Git available on `PATH`

## Usage

Run the analyzer from any Git repository:

```powershell
python -m repo_health_agent --path C:\path\to\repository
```

The default output is a concise human-readable report. Use JSON for automation:

```powershell
python -m repo_health_agent --path . --format json
```

To run the CLI directly from this repository without installing a package:

```powershell
$env:PYTHONPATH = "src"
python -m repo_health_agent --path C:\path\to\repository
```

The report evaluates:

- repository accessibility and current branch
- recent commit activity
- working-tree cleanliness
- README, license, CI, tests, and dependency metadata

The score is intentionally a transparent heuristic, not a security audit. Every
check includes its status, score contribution, and explanation in JSON output.

## Development

Run the test suite from the repository root:

```powershell
python -m unittest discover -s tests -v
```
