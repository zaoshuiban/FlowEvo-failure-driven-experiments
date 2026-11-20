"""Minimal Python sandbox backed by tempfile and subprocess."""

from __future__ import annotations

import json
from contextlib import contextmanager
import subprocess
import tempfile
from pathlib import Path


class Sandbox:
    """Execute Python snippets in an isolated temporary file."""

    def __init__(self, python_executable: str = "python", timeout_seconds: float = 5.0) -> None:
        """Initialize sandbox settings.

        Args:
            python_executable: Python interpreter used for execution.
            timeout_seconds: Max wall-clock execution time.
        """
        self.python_executable = python_executable
        self.timeout_seconds = timeout_seconds
        self.dependencies = {}
        self.skill_events = []

    @contextmanager
    def bind_dependencies(self, dependencies):
        from failure_evo.skill_runtime import validate_bundle
        validate_bundle(dependencies)
        previous = self.dependencies
        self.dependencies = dependencies
        self.skill_events = []
        try:
            yield self
        finally:
            self.dependencies = previous

    def run(self, code: str, module_bundle=None) -> dict:
        """Run Python code in a temporary file.

        Args:
            code: Complete Python program to execute.

        Returns:
            A dict containing stdout/stderr/returncode/passed/timeout.
        """
        with tempfile.TemporaryDirectory(prefix="idea_v7_") as tmp_dir:
            script_path = Path(tmp_dir) / "main.py"
            script_path.write_text(code, encoding="utf-8")
            bundle = self.dependencies if module_bundle is None else module_bundle
            event_file = None
            if bundle:
                from failure_evo.skill_runtime import materialize
                event_file = materialize(bundle, Path(tmp_dir))
            try:
                result = subprocess.run(
                    [self.python_executable, str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                    "passed": result.returncode == 0,
                    "timeout": False,
                }
            except subprocess.TimeoutExpired as exc:
                return {
                    "stdout": exc.stdout or "",
                    "stderr": exc.stderr or "",
                    "returncode": -1,
                    "passed": False,
                    "timeout": True,
                }

            finally:
                if event_file and event_file.exists():
                    self.skill_events.extend(json.loads(line) for line in event_file.read_text().splitlines())
