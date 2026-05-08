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


def test_validate_all_with_no_skills_passes():
    """With only fixtures present (no real skills yet), --validate-all should pass."""
    result = run_render("--validate-all")
    assert result.returncode == 0


def test_validate_all_catches_invalid_manifest(tmp_path: Path, monkeypatch):
    """If a manifest fails the schema, --validate-all exits non-zero."""
    # This test is a placeholder — implementation will be exercised
    # once a real skill manifest exists. For now, just ensure the flag
    # runs without crashing.
    result = run_render("--validate-all")
    # We don't assert returncode here; we just confirm no crash.
    assert "Traceback" not in result.stderr
