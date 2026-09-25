import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from repo_health_agent.analyzer import analyze_repository
from repo_health_agent.cli import main


class AnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        subprocess.run(["git", "init", "-b", "main", str(self.repo)], check=True, capture_output=True)
        (self.repo / "README.md").write_text("# Example\n", encoding="utf-8")
        (self.repo / "LICENSE").write_text("MIT\n", encoding="utf-8")
        (self.repo / "tests").mkdir()
        (self.repo / ".github" / "workflows").mkdir(parents=True)
        (self.repo / "pyproject.toml").write_text("[project]\nname='example'\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-m", "Initial"], check=True, capture_output=True)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_report_contains_all_checks_and_score(self):
        report = analyze_repository(self.repo)
        self.assertEqual(report["status"], "healthy")
        self.assertGreaterEqual(report["percentage"], 80)
        self.assertLessEqual(report["percentage"], 100)
        self.assertEqual(report["max_score"], 100)
        self.assertEqual(len(report["checks"]), 8)

    def test_uncommitted_changes_are_reported(self):
        (self.repo / "README.md").write_text("# Changed\n", encoding="utf-8")
        report = analyze_repository(self.repo)
        working_tree = next(check for check in report["checks"] if check["name"] == "working_tree")
        self.assertEqual(working_tree["status"], "warn")

    def test_cli_json_output(self):
        from io import StringIO
        import contextlib

        output = StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = main(["--path", str(self.repo), "--format", "json"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(output.getvalue())["repository"], str(self.repo))

    def test_missing_repository_is_rejected(self):
        with self.assertRaises(ValueError):
            analyze_repository(self.repo / "missing")
