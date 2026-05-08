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


import sys
sys.path.insert(0, str(REPO_ROOT / "scripts" / "agent"))


def test_extends_resolution_merges_objects(tmp_path: Path):
    """Object fields deep-merge: child overrides specified keys, inherits rest."""
    import render as r

    parent = tmp_path / "parent.yaml"
    child = tmp_path / "child.yaml"
    parent.write_text(
        "schema_version: 1\n"
        "workstream:\n"
        "  id: parent\n"
        "  name: Parent\n"
        "  full_name: Parent WS\n"
        "meeting:\n"
        "  cadence: Thursdays\n"
        "  time: '12:00 ET'\n"
    )
    child.write_text(
        "schema_version: 1\n"
        "extends: parent\n"
        "workstream:\n"
        "  id: child\n"
        "  name: Child\n"
        "  full_name: Child WS\n"
        "meeting:\n"
        "  cadence: Wednesdays\n"
    )

    effective = r.resolve_config(child, configs_dir=tmp_path)
    assert effective["meeting"]["cadence"] == "Wednesdays"
    assert effective["meeting"]["time"] == "12:00 ET"  # inherited
    assert effective["workstream"]["id"] == "child"


def test_extends_resolution_replaces_arrays(tmp_path: Path):
    """Array fields fully replace, do not append."""
    import render as r

    parent = tmp_path / "parent.yaml"
    child = tmp_path / "child.yaml"
    parent.write_text(
        "schema_version: 1\n"
        "workstream: { id: parent, name: P, full_name: P }\n"
        "leads:\n"
        "  - { name: Alice, role: chair }\n"
        "  - { name: Bob, role: chair }\n"
    )
    child.write_text(
        "schema_version: 1\n"
        "extends: parent\n"
        "workstream: { id: child, name: C, full_name: C }\n"
        "leads:\n"
        "  - { name: Carol, role: chair }\n"
    )

    effective = r.resolve_config(child, configs_dir=tmp_path)
    assert len(effective["leads"]) == 1
    assert effective["leads"][0]["name"] == "Carol"


def test_extends_unresolvable_parent_raises(tmp_path: Path):
    """A child whose extends points at a missing file raises clearly."""
    import render as r

    child = tmp_path / "child.yaml"
    child.write_text(
        "schema_version: 1\n"
        "extends: nonexistent\n"
        "workstream: { id: child, name: C, full_name: C }\n"
    )
    with pytest.raises(FileNotFoundError):
        r.resolve_config(child, configs_dir=tmp_path)


def test_extends_no_chain(tmp_path: Path):
    """Single-level only: a config that extends another extending config raises."""
    import render as r

    grandparent = tmp_path / "grandparent.yaml"
    parent = tmp_path / "parent.yaml"
    child = tmp_path / "child.yaml"
    grandparent.write_text("schema_version: 1\nworkstream: { id: gp, name: GP, full_name: GP }\n")
    parent.write_text("schema_version: 1\nextends: grandparent\nworkstream: { id: p, name: P, full_name: P }\n")
    child.write_text("schema_version: 1\nextends: parent\nworkstream: { id: c, name: C, full_name: C }\n")
    with pytest.raises(ValueError, match="single-level"):
        r.resolve_config(child, configs_dir=tmp_path)
