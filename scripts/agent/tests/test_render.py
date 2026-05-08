"""Renderer tests for scripts/agent/render.py."""
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
RENDER = REPO_ROOT / "scripts" / "agent" / "render.py"
PYTHON = "/Users/sarahnovotny/Github/python3.12-venv/bin/python3"


def run_render(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, str(RENDER), *args],
        capture_output=True,
        text=True,
    )


def test_render_runs_with_help():
    result = run_render("--help")
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower() or "usage:" in result.stderr.lower()


def test_render_no_args_errors():
    result = run_render()
    assert result.returncode != 0
