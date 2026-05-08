# CoSAI Agent Skills v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land `scripts/agent/` infrastructure with manifest schema, migrated agenda + triage skills, WS4 workstream config, Claude Code renderer, `agenda_drafts/` canonical location, `fetch_meeting_minutes.py` sync, docs, and CI gate.

**Architecture:** Co-equal `manifest.yaml` (structured contracts) + `SKILL.md` (imperative process narrative). Renderer reads manifest, builds Claude Code frontmatter, stitches with SKILL.md, substitutes repo-absolute paths, places files in `~/.claude/skills/<skill>/` (symlink default). Workstream configs use single-level inheritance via `extends:`.

**Tech Stack:** Python 3.12 (`~/Github/python3.12-venv/`), `pyyaml`, `jsonschema`, `pytest`. `gh` CLI at `/opt/homebrew/bin/gh` for GitHub. Markdown + YAML + JSON for artefacts. GitHub Actions for CI.

**Branch:** `tooling/agent-skills` (already created off `reorg`). All commits use the CoSAI vendor-neutral attribution trailer:

```
Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
```

**Source spec:** `scripts/agent/DESIGN.md` (725 lines, committed on this branch).

---

## File Structure

### Created files

```
scripts/agent/
├── DESIGN.md                                       # already exists
├── PLAN.md                                         # this file
├── README.md                                       # entry point
├── MANIFEST_SCHEMA.md                              # human-readable manifest reference
├── manifest.schema.json                            # JSON Schema for manifests
├── render.py                                       # CLI renderer
├── requirements.txt                                # pyyaml, jsonschema (runtime)
├── requirements-dev.txt                            # adds pytest
├── pytest.ini                                      # pytest config
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_validate.py                            # schema validation tests
│   ├── test_render.py                              # renderer tests
│   └── fixtures/
│       ├── valid_manifest.yaml
│       ├── invalid_manifest_missing_field.yaml
│       ├── valid_config.yaml
│       └── invalid_config_extends_loop.yaml
├── configs/
│   ├── _config.schema.json                         # JSON Schema for configs
│   └── ws4.yaml                                    # WS4 workstream config
├── cosai-meeting-agenda/
│   ├── manifest.yaml
│   └── SKILL.md
├── cosai-issue-triage/
│   ├── manifest.yaml
│   ├── SKILL.md
│   └── triage_milestones.json
└── parity-reports/
    ├── cosai-meeting-agenda-2026-05-08.md
    └── cosai-issue-triage-2026-05-08.md

agenda_drafts/
├── README.md                                       # explains the convention
└── ws4/
    └── .gitkeep

.github/
└── workflows/
    └── agent-validate.yml                          # CI gate
```

### Modified files

| Path | Change |
|---|---|
| `scripts/fetch_meeting_minutes.py` | Sync from working copy at `~/Github/scripts/fetch_meeting_minutes.py` (adds WS3 + Code-SIG + RM-SIG sources, `HttpError`-resilient export path) |
| `CONTRIBUTING.md` | Add a one-paragraph "Working with WS4 tooling" section pointing at `scripts/agent/README.md` |
| `CLAUDE.md` | (working-tree only, do not stage if currently untracked) Update to describe only the new `scripts/agent/` pathway |

### Source-of-truth files for the migration

| New path | Source it migrates from | Notes |
|---|---|---|
| `scripts/agent/cosai-meeting-agenda/SKILL.md` | `~/Github/ws4-secure-design-agentic-systems/.claude/skills.bak/agenda/SKILL.md` | Same content as `sarahnovotny/cosai-claude/skills/agenda/SKILL.md` (zero drift) |
| `scripts/agent/cosai-issue-triage/SKILL.md` | `~/Github/ws4-secure-design-agentic-systems/.claude/skills.bak/triage/SKILL.md` | Same content as `sarahnovotny/cosai-claude/skills/triage/SKILL.md` |
| `scripts/agent/cosai-issue-triage/triage_milestones.json` | `~/Github/ws4-secure-design-agentic-systems/.claude/skills.bak/triage/triage_metadata.json` | Re-shaped from flat array to `{ "namespaces": { "ws4": { "milestones": [...] } } }` |

---

## Pre-flight: dev environment

The shared venv at `/Users/sarahnovotny/Github/python3.12-venv/` has `pyyaml` (5.1) and `jsonschema` (4.26.0) but is missing `pytest`. Task 0 below installs it.

---

## Task 0: Install pytest into the shared venv

**Files:** none

- [ ] **Step 1: Install pytest**

```bash
/Users/sarahnovotny/Github/python3.12-venv/bin/pip install 'pytest>=8.0'
```

Expected: pytest installed; no errors.

- [ ] **Step 2: Verify install**

```bash
/Users/sarahnovotny/Github/python3.12-venv/bin/python3 -c "import pytest; print(pytest.__version__)"
```

Expected: a version string ≥ 8.0.

- [ ] **Step 3: Commit nothing.** This is a local environment change, not a repo change.

---

## Task 1: Add Python dependency files

**Files:**
- Create: `scripts/agent/requirements.txt`
- Create: `scripts/agent/requirements-dev.txt`
- Create: `scripts/agent/pytest.ini`

- [ ] **Step 1: Write `scripts/agent/requirements.txt`**

```
pyyaml>=5.1
jsonschema>=4.0
```

- [ ] **Step 2: Write `scripts/agent/requirements-dev.txt`**

```
-r requirements.txt
pytest>=8.0
```

- [ ] **Step 3: Write `scripts/agent/pytest.ini`**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -ra --strict-markers
```

- [ ] **Step 4: Commit**

```bash
git add scripts/agent/requirements.txt scripts/agent/requirements-dev.txt scripts/agent/pytest.ini
git commit -m "$(cat <<'EOF'
chore(scripts/agent): add Python dependency files and pytest config

Establishes the runtime + dev dependency set and pytest layout for the
new scripts/agent/ tooling. requirements.txt covers what render.py needs
at runtime; requirements-dev.txt adds pytest.

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 2: Scaffold `scripts/agent/tests/` directory

**Files:**
- Create: `scripts/agent/tests/__init__.py` (empty)
- Create: `scripts/agent/tests/conftest.py`
- Create: `scripts/agent/tests/fixtures/.gitkeep` (empty)

- [ ] **Step 1: Write `scripts/agent/tests/__init__.py`**

Empty file (just creates the package).

- [ ] **Step 2: Write `scripts/agent/tests/conftest.py`**

```python
"""Shared pytest fixtures for scripts/agent/ tests."""
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
AGENT_DIR = REPO_ROOT / "scripts" / "agent"


@pytest.fixture
def agent_dir() -> Path:
    """Absolute path to scripts/agent/ in the repo."""
    return AGENT_DIR


@pytest.fixture
def fixtures_dir() -> Path:
    """Absolute path to scripts/agent/tests/fixtures/."""
    return Path(__file__).parent / "fixtures"
```

- [ ] **Step 3: Write `scripts/agent/tests/fixtures/.gitkeep`**

Empty file.

- [ ] **Step 4: Smoke-check pytest discovers tests dir**

```bash
cd /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent && /Users/sarahnovotny/Github/python3.12-venv/bin/pytest --collect-only -q
```

Expected: `no tests collected` (no failures, just empty).

- [ ] **Step 5: Commit**

```bash
git add scripts/agent/tests/__init__.py scripts/agent/tests/conftest.py scripts/agent/tests/fixtures/.gitkeep
git commit -m "$(cat <<'EOF'
chore(scripts/agent): scaffold tests/ directory and conftest

Adds an empty tests/ package with a conftest.py that exposes agent_dir
and fixtures_dir fixtures for downstream tests.

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 3: Write `manifest.schema.json` (manifest contract)

**Files:**
- Create: `scripts/agent/manifest.schema.json`

This schema enforces the manifest fields documented in DESIGN.md §5.

- [ ] **Step 1: Write `scripts/agent/manifest.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://cosai-oasis.github.io/ws4/manifest.schema.json",
  "title": "CoSAI Agent Skill Manifest",
  "type": "object",
  "required": [
    "schema_version",
    "name",
    "description",
    "version",
    "governance",
    "arguments",
    "dependencies",
    "output",
    "boundaries",
    "failure_modes",
    "narrative"
  ],
  "properties": {
    "schema_version": { "type": "integer", "const": 1 },
    "name": { "type": "string", "pattern": "^[a-z][a-z0-9-]*$" },
    "description": { "type": "string", "minLength": 10 },
    "version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+(-[a-z0-9-]+)?$" },
    "governance": {
      "type": "object",
      "required": ["license", "ai_attribution"],
      "properties": {
        "license": { "type": "string" },
        "ai_attribution": { "type": "string" }
      }
    },
    "arguments": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "type", "required"],
        "properties": {
          "name": { "type": "string" },
          "type": { "type": "string", "enum": ["string", "integer", "boolean", "array"] },
          "required": { "type": "boolean" },
          "description": { "type": "string" }
        }
      }
    },
    "dependencies": {
      "type": "object",
      "required": ["tools"],
      "properties": {
        "tools": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["id", "required", "capabilities"],
            "properties": {
              "id": { "type": "string" },
              "purpose": { "type": "string" },
              "required": { "type": "boolean" },
              "capabilities": {
                "type": "array",
                "items": { "type": "string", "enum": ["read", "write", "exec"] }
              }
            }
          }
        },
        "configs": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["path"],
            "properties": {
              "path": { "type": "string" },
              "schema": { "type": "string" }
            }
          }
        },
        "data": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["path", "access", "runtime_role", "provisioning"],
            "properties": {
              "path": { "type": "string" },
              "access": { "type": "string", "enum": ["read", "write", "read-write"] },
              "runtime_role": { "type": "string", "enum": ["input", "output"] },
              "provisioning": {
                "type": "object",
                "required": ["kind", "tracked_in_repo"],
                "properties": {
                  "kind": { "type": "string", "enum": ["in-repo", "out-of-band", "runtime-fetched"] },
                  "tracked_in_repo": { "type": "boolean" },
                  "populated_by": {
                    "type": "object",
                    "properties": {
                      "tool": { "type": "string" },
                      "repo": { "type": "string" },
                      "documented_at": { "type": "string" }
                    }
                  },
                  "cadence": { "type": "string" },
                  "on_missing": { "type": "string" }
                }
              }
            }
          }
        }
      }
    },
    "composition": {
      "type": "object",
      "properties": {
        "calls": { "type": "array", "items": { "type": "object" } },
        "called_by": { "type": "array", "items": { "type": "object" } }
      }
    },
    "output": {
      "type": "object",
      "required": ["primary"],
      "properties": {
        "primary": {
          "type": "object",
          "required": ["type", "location"],
          "properties": {
            "type": { "type": "string" },
            "location": { "type": "string" },
            "frontmatter": { "type": "object" }
          }
        },
        "side_effects": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["kind", "condition", "action"],
            "properties": {
              "kind": { "type": "string" },
              "condition": { "type": "string" },
              "action": { "type": "string" },
              "v1_status": { "type": "string", "enum": ["implemented", "deferred"] }
            }
          }
        }
      }
    },
    "boundaries": {
      "type": "object",
      "required": ["does_not"],
      "properties": {
        "does_not": { "type": "array", "items": { "type": "string" }, "minItems": 1 }
      }
    },
    "failure_modes": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["condition", "action"],
        "properties": {
          "condition": { "type": "string" },
          "action": { "type": "string" }
        }
      }
    },
    "narrative": { "type": "string", "default": "SKILL.md" }
  },
  "additionalProperties": false
}
```

- [ ] **Step 2: Validate the JSON parses**

```bash
/Users/sarahnovotny/Github/python3.12-venv/bin/python3 -c "import json; json.load(open('/Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent/manifest.schema.json'))"
```

Expected: no error.

- [ ] **Step 3: Commit**

```bash
git add scripts/agent/manifest.schema.json
git commit -m "$(cat <<'EOF'
feat(scripts/agent): add manifest.schema.json for skill manifests

JSON Schema 2020-12 enforcing the manifest contract documented in
scripts/agent/DESIGN.md §5: schema_version, name, version, governance,
arguments, dependencies (tools/configs/data with provisioning),
composition, output, boundaries, failure_modes, narrative.

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 4: Write fixture manifests + first validation tests (TDD)

**Files:**
- Create: `scripts/agent/tests/fixtures/valid_manifest.yaml`
- Create: `scripts/agent/tests/fixtures/invalid_manifest_missing_field.yaml`
- Create: `scripts/agent/tests/test_validate.py`

- [ ] **Step 1: Write the failing test first**

`scripts/agent/tests/test_validate.py`:

```python
"""Schema validation tests for scripts/agent/."""
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def manifest_schema(agent_dir: Path) -> dict:
    return load_json(agent_dir / "manifest.schema.json")


def test_manifest_schema_loads(manifest_schema: dict):
    Draft202012Validator.check_schema(manifest_schema)


def test_valid_manifest_passes(manifest_schema: dict, fixtures_dir: Path):
    manifest = load_yaml(fixtures_dir / "valid_manifest.yaml")
    Draft202012Validator(manifest_schema).validate(manifest)


def test_invalid_manifest_missing_field_fails(manifest_schema: dict, fixtures_dir: Path):
    manifest = load_yaml(fixtures_dir / "invalid_manifest_missing_field.yaml")
    with pytest.raises(ValidationError):
        Draft202012Validator(manifest_schema).validate(manifest)
```

- [ ] **Step 2: Run the test — expect failures**

```bash
cd /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent && /Users/sarahnovotny/Github/python3.12-venv/bin/pytest tests/test_validate.py -v
```

Expected: 2 of 3 tests fail because fixture YAML files don't exist yet. (The `test_manifest_schema_loads` should pass — schema file exists.)

- [ ] **Step 3: Write `valid_manifest.yaml` fixture**

```yaml
schema_version: 1
name: example-skill
description: |
  An example skill manifest used as a test fixture for validating
  manifest.schema.json. Not a real skill.
version: 0.1.0
governance:
  license: CC-BY-4.0
  ai_attribution: |
    Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
arguments:
  - name: target
    type: string
    required: true
    description: The thing to operate on.
dependencies:
  tools:
    - id: filesystem
      purpose: read inputs, write outputs
      required: true
      capabilities: [read, write]
output:
  primary:
    type: markdown
    location: out/{target}.md
boundaries:
  does_not:
    - Modify inputs
failure_modes:
  - condition: input not found
    action: halt with the expected path
narrative: SKILL.md
```

- [ ] **Step 4: Write `invalid_manifest_missing_field.yaml` fixture**

Same as the valid one, but **omit the `name` field** to make it invalid.

```yaml
schema_version: 1
description: |
  An example skill manifest missing the required `name` field.
version: 0.1.0
governance:
  license: CC-BY-4.0
  ai_attribution: |
    Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
arguments:
  - name: target
    type: string
    required: true
dependencies:
  tools:
    - id: filesystem
      required: true
      capabilities: [read, write]
output:
  primary:
    type: markdown
    location: out/{target}.md
boundaries:
  does_not:
    - Modify inputs
failure_modes:
  - condition: input not found
    action: halt
narrative: SKILL.md
```

- [ ] **Step 5: Run tests — expect all 3 to pass**

```bash
cd /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent && /Users/sarahnovotny/Github/python3.12-venv/bin/pytest tests/test_validate.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/agent/tests/test_validate.py scripts/agent/tests/fixtures/valid_manifest.yaml scripts/agent/tests/fixtures/invalid_manifest_missing_field.yaml
git commit -m "$(cat <<'EOF'
test(scripts/agent): add manifest schema validation tests + fixtures

Three tests: schema loadable; valid manifest passes; invalid manifest
(missing required `name`) fails with ValidationError. Establishes the
pattern for fixture-driven schema tests.

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 5: Write `_config.schema.json` (workstream config contract)

**Files:**
- Create: `scripts/agent/configs/_config.schema.json`

- [ ] **Step 1: Write `scripts/agent/configs/_config.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://cosai-oasis.github.io/ws4/config.schema.json",
  "title": "CoSAI Agent Skill Workstream Config",
  "type": "object",
  "required": ["schema_version", "workstream"],
  "properties": {
    "schema_version": { "type": "integer", "const": 1 },
    "extends": { "type": "string", "pattern": "^[a-z][a-z0-9-]*$" },
    "workstream": {
      "type": "object",
      "required": ["id", "name", "full_name"],
      "properties": {
        "id": { "type": "string", "pattern": "^[a-z][a-z0-9-]*$" },
        "name": { "type": "string" },
        "full_name": { "type": "string" },
        "parent_workstream": { "type": ["string", "null"] }
      }
    },
    "repo": {
      "type": "object",
      "properties": {
        "owner": { "type": "string" },
        "name": { "type": "string" }
      }
    },
    "leads": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "role"],
        "properties": {
          "name": { "type": "string" },
          "github": { "type": ["string", "null"] },
          "role": { "type": "string", "enum": ["chair", "supporting", "contributor"] }
        }
      }
    },
    "meeting": {
      "type": "object",
      "properties": {
        "cadence": { "type": "string" },
        "time": { "type": "string" },
        "meeting_minutes_dir": { "type": "string" },
        "filename_pattern": { "type": "string" },
        "agenda_template_discussion": { "type": ["integer", "null"] },
        "agenda_section_template": { "type": "string" },
        "fallback_minutes_dir": { "type": ["string", "null"] }
      }
    },
    "channels": {
      "type": "object",
      "properties": {
        "slack": {
          "type": "object",
          "properties": {
            "workspace": { "type": "string" },
            "channel": { "type": "string" }
          }
        },
        "mailing_list": { "type": "string" }
      }
    },
    "triage": {
      "type": "object",
      "properties": {
        "milestones_file": { "type": "string" },
        "milestone_namespace": { "type": "string" },
        "recognised_triage_labels": {
          "type": "array",
          "items": { "type": "string" }
        },
        "chair_label_authority": { "type": "boolean" }
      }
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 2: Validate JSON parses**

```bash
/Users/sarahnovotny/Github/python3.12-venv/bin/python3 -c "import json; json.load(open('/Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent/configs/_config.schema.json'))"
```

Expected: no error.

- [ ] **Step 3: Commit**

```bash
git add scripts/agent/configs/_config.schema.json
git commit -m "$(cat <<'EOF'
feat(scripts/agent): add _config.schema.json for workstream configs

JSON Schema enforcing the workstream config contract from DESIGN.md §6:
schema_version, optional extends, workstream identity, repo, leads,
meeting, channels, triage. Used by render.py --validate-all and pytest.

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 6: Add config validation tests (TDD)

**Files:**
- Create: `scripts/agent/tests/fixtures/valid_config.yaml`
- Create: `scripts/agent/tests/fixtures/invalid_config_extends_loop.yaml`
- Modify: `scripts/agent/tests/test_validate.py`

- [ ] **Step 1: Append config tests to `test_validate.py`**

Add at the bottom of `scripts/agent/tests/test_validate.py`:

```python
@pytest.fixture
def config_schema(agent_dir: Path) -> dict:
    return load_json(agent_dir / "configs" / "_config.schema.json")


def test_config_schema_loads(config_schema: dict):
    Draft202012Validator.check_schema(config_schema)


def test_valid_config_passes(config_schema: dict, fixtures_dir: Path):
    config = load_yaml(fixtures_dir / "valid_config.yaml")
    Draft202012Validator(config_schema).validate(config)


def test_config_with_extends_passes_schema(config_schema: dict, fixtures_dir: Path):
    """Schema does NOT enforce that extends resolves; that's render.py's job."""
    config = load_yaml(fixtures_dir / "invalid_config_extends_loop.yaml")
    # Schema-level validation passes — extends references are resolved
    # by the renderer, which catches loops separately (see test_render.py).
    Draft202012Validator(config_schema).validate(config)
```

- [ ] **Step 2: Write `valid_config.yaml`**

```yaml
schema_version: 1
workstream:
  id: example-ws
  name: Example WS
  full_name: Example Workstream — Test Fixture
  parent_workstream: null
repo:
  owner: cosai-oasis
  name: example-repo
leads:
  - name: Example Person
    github: example
    role: chair
meeting:
  cadence: Mondays
  time: "10:00 ET"
  meeting_minutes_dir: meeting_minutes/example
  filename_pattern: "EX-{YYYYMMDD}.md"
channels:
  mailing_list: example@example.org
triage:
  milestones_file: ../some-skill/triage_milestones.json
  milestone_namespace: example-ws
  recognised_triage_labels:
    - review
  chair_label_authority: true
```

- [ ] **Step 3: Write `invalid_config_extends_loop.yaml`**

```yaml
schema_version: 1
extends: nonexistent-parent
workstream:
  id: looper
  name: Looper
  full_name: A config whose extends does not resolve to anything
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent && /Users/sarahnovotny/Github/python3.12-venv/bin/pytest tests/test_validate.py -v
```

Expected: 6 passed (3 manifest + 3 config).

- [ ] **Step 5: Commit**

```bash
git add scripts/agent/tests/test_validate.py scripts/agent/tests/fixtures/valid_config.yaml scripts/agent/tests/fixtures/invalid_config_extends_loop.yaml
git commit -m "$(cat <<'EOF'
test(scripts/agent): add config schema validation tests + fixtures

Three tests: schema loadable; valid config passes; config with
unresolvable extends still passes the schema (loops are caught by
render.py, not the schema).

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 7: `render.py` — argparse skeleton

**Files:**
- Create: `scripts/agent/render.py`

- [ ] **Step 1: Write `scripts/agent/tests/test_render.py` with the skeleton test (TDD)**

```python
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
```

- [ ] **Step 2: Run the test — expect failure (file does not exist)**

```bash
cd /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent && /Users/sarahnovotny/Github/python3.12-venv/bin/pytest tests/test_render.py -v
```

Expected: failures because `render.py` does not exist yet.

- [ ] **Step 3: Write `scripts/agent/render.py` skeleton**

```python
#!/usr/bin/env python3
"""Render CoSAI agent skills for a target harness.

See scripts/agent/DESIGN.md §8 for behaviour.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = REPO_ROOT / "scripts" / "agent"
CONFIGS_DIR = AGENT_DIR / "configs"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="render.py",
        description="Render CoSAI agent skills for a target harness.",
    )
    p.add_argument("skill", nargs="?", help="Skill directory name (e.g. cosai-meeting-agenda).")
    p.add_argument("--target", choices=["claude-code", "generic"], default="claude-code")
    p.add_argument("--config", help="Workstream config slug (e.g. ws4) for path substitution.")
    p.add_argument("--output", help="Override destination directory.")
    p.add_argument("--symlink", action="store_true", default=True, help="Symlink files (default).")
    p.add_argument("--copy", dest="symlink", action="store_false", help="Copy files instead of symlinking.")
    p.add_argument("--dry-run", action="store_true", help="Validate and print intent; do not write.")
    p.add_argument("--validate-all", action="store_true", help="Validate every manifest and config; exit non-zero on failure.")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.validate_all:
        return _cmd_validate_all()

    if not args.skill:
        parser.error("the following arguments are required: skill (or use --validate-all)")

    # Stub for now; real dispatch comes in later tasks.
    print(f"render.py: skill={args.skill} target={args.target} (stub)", file=sys.stderr)
    return 0


def _cmd_validate_all() -> int:
    """Stub; real implementation in a later task."""
    print("render.py --validate-all (stub)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Make `render.py` executable**

```bash
chmod +x /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent/render.py
```

- [ ] **Step 5: Run the test — expect pass**

```bash
cd /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent && /Users/sarahnovotny/Github/python3.12-venv/bin/pytest tests/test_render.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/agent/render.py scripts/agent/tests/test_render.py
git commit -m "$(cat <<'EOF'
feat(scripts/agent): render.py argparse skeleton + initial tests

CLI accepts a skill positional, --target {claude-code,generic} (default
claude-code), --config, --output, --symlink/--copy (default symlink),
--dry-run, --validate-all. Real behaviour added in subsequent tasks.

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 8: `render.py` — manifest loader and validator

**Files:**
- Modify: `scripts/agent/render.py`
- Modify: `scripts/agent/tests/test_render.py`

- [ ] **Step 1: Add a failing test for manifest loading**

Append to `tests/test_render.py`:

```python
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
```

- [ ] **Step 2: Run tests — first new test passes (stub), second passes vacuously**

```bash
cd /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent && /Users/sarahnovotny/Github/python3.12-venv/bin/pytest tests/test_render.py -v
```

Expected: 4 passed.

- [ ] **Step 3: Implement manifest loader + validator in `render.py`**

Replace the contents of `scripts/agent/render.py` with:

```python
#!/usr/bin/env python3
"""Render CoSAI agent skills for a target harness.

See scripts/agent/DESIGN.md §8 for behaviour.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = REPO_ROOT / "scripts" / "agent"
CONFIGS_DIR = AGENT_DIR / "configs"
MANIFEST_SCHEMA_PATH = AGENT_DIR / "manifest.schema.json"
CONFIG_SCHEMA_PATH = CONFIGS_DIR / "_config.schema.json"


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f)


def _load_json(path: Path) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def _load_manifest(skill_dir: Path) -> dict[str, Any]:
    return _load_yaml(skill_dir / "manifest.yaml")


def _validate_manifest(manifest: dict[str, Any]) -> list[str]:
    """Return list of validation error messages; empty if valid."""
    schema = _load_json(MANIFEST_SCHEMA_PATH)
    errors = []
    for err in Draft202012Validator(schema).iter_errors(manifest):
        path = "/".join(str(p) for p in err.path) or "<root>"
        errors.append(f"{path}: {err.message}")
    return errors


def _validate_config(config: dict[str, Any]) -> list[str]:
    schema = _load_json(CONFIG_SCHEMA_PATH)
    errors = []
    for err in Draft202012Validator(schema).iter_errors(config):
        path = "/".join(str(p) for p in err.path) or "<root>"
        errors.append(f"{path}: {err.message}")
    return errors


def _list_skill_dirs() -> list[Path]:
    """Return all directories under scripts/agent/ that contain a manifest.yaml."""
    skills = []
    for entry in sorted(AGENT_DIR.iterdir()):
        if entry.is_dir() and (entry / "manifest.yaml").exists():
            skills.append(entry)
    return skills


def _list_config_files() -> list[Path]:
    """Return all top-level workstream configs (configs/<id>.yaml)."""
    return sorted(p for p in CONFIGS_DIR.glob("*.yaml") if not p.name.startswith("_"))


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="render.py",
        description="Render CoSAI agent skills for a target harness.",
    )
    p.add_argument("skill", nargs="?", help="Skill directory name (e.g. cosai-meeting-agenda).")
    p.add_argument("--target", choices=["claude-code", "generic"], default="claude-code")
    p.add_argument("--config", help="Workstream config slug (e.g. ws4) for path substitution.")
    p.add_argument("--output", help="Override destination directory.")
    p.add_argument("--symlink", action="store_true", default=True, help="Symlink files (default).")
    p.add_argument("--copy", dest="symlink", action="store_false", help="Copy files instead of symlinking.")
    p.add_argument("--dry-run", action="store_true", help="Validate and print intent; do not write.")
    p.add_argument("--validate-all", action="store_true", help="Validate every manifest and config; exit non-zero on failure.")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.validate_all:
        return _cmd_validate_all()

    if not args.skill:
        parser.error("the following arguments are required: skill (or use --validate-all)")

    print(f"render.py: skill={args.skill} target={args.target} (target rendering not yet implemented)", file=sys.stderr)
    return 0


def _cmd_validate_all() -> int:
    """Walk scripts/agent/, validate every manifest.yaml and config; exit non-zero on failure."""
    failures: list[str] = []

    for skill_dir in _list_skill_dirs():
        try:
            manifest = _load_manifest(skill_dir)
        except Exception as e:
            failures.append(f"{skill_dir.name}/manifest.yaml: parse error: {e}")
            continue
        errors = _validate_manifest(manifest)
        if errors:
            for e in errors:
                failures.append(f"{skill_dir.name}/manifest.yaml: {e}")
        else:
            print(f"OK   {skill_dir.name}/manifest.yaml", file=sys.stderr)

    for config_path in _list_config_files():
        try:
            config = _load_yaml(config_path)
        except Exception as e:
            failures.append(f"configs/{config_path.name}: parse error: {e}")
            continue
        errors = _validate_config(config)
        if errors:
            for e in errors:
                failures.append(f"configs/{config_path.name}: {e}")
        else:
            print(f"OK   configs/{config_path.name}", file=sys.stderr)

    if failures:
        print("\nValidation failures:", file=sys.stderr)
        for f in failures:
            print(f"  FAIL {f}", file=sys.stderr)
        return 1
    print("\nAll manifests and configs valid.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent && /Users/sarahnovotny/Github/python3.12-venv/bin/pytest tests/test_render.py -v
```

Expected: 4 passed (no real skills exist yet, so `--validate-all` reports "all valid" trivially).

- [ ] **Step 5: Run validate-all manually to confirm output**

```bash
/Users/sarahnovotny/Github/python3.12-venv/bin/python3 /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent/render.py --validate-all
```

Expected: prints "All manifests and configs valid." and exits 0.

- [ ] **Step 6: Commit**

```bash
git add scripts/agent/render.py scripts/agent/tests/test_render.py
git commit -m "$(cat <<'EOF'
feat(scripts/agent): render.py manifest+config loader and --validate-all

Walks scripts/agent/ for any directory containing manifest.yaml and any
configs/*.yaml (excluding _-prefixed files like _config.schema.json),
loads + validates each against the appropriate JSON Schema. Exits 1 on
any failure with a per-file path.

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 9: `render.py` — config `extends` resolver

**Files:**
- Modify: `scripts/agent/render.py`
- Modify: `scripts/agent/tests/test_render.py`

- [ ] **Step 1: Write failing tests for extends resolution**

Append to `tests/test_render.py`:

```python
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
```

- [ ] **Step 2: Run tests — expect failures**

```bash
cd /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent && /Users/sarahnovotny/Github/python3.12-venv/bin/pytest tests/test_render.py::test_extends_resolution_merges_objects -v
```

Expected: AttributeError or NameError on `r.resolve_config`.

- [ ] **Step 3: Add `resolve_config` to `render.py`**

After the existing `_validate_config` function in `render.py`, add:

```python
def _deep_merge(parent: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge child onto parent. Object fields merge; arrays fully replace; scalars override; null clears."""
    if not isinstance(parent, dict) or not isinstance(child, dict):
        return child
    result = dict(parent)
    for key, child_val in child.items():
        if child_val is None and key in result:
            del result[key]
            continue
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(child_val, dict)
        ):
            result[key] = _deep_merge(result[key], child_val)
        else:
            # Scalars and arrays replace.
            result[key] = child_val
    return result


def resolve_config(config_path: Path, configs_dir: Path | None = None) -> dict[str, Any]:
    """Load a config, resolving a single-level `extends:` chain.

    Raises FileNotFoundError if extends points at a missing parent.
    Raises ValueError if a chain longer than one level is encountered.
    """
    configs_dir = configs_dir or CONFIGS_DIR
    config = _load_yaml(config_path)

    parent_id = config.get("extends")
    if not parent_id:
        return config

    parent_path = configs_dir / f"{parent_id}.yaml"
    if not parent_path.exists():
        raise FileNotFoundError(
            f"{config_path.name}: extends '{parent_id}' but {parent_path} does not exist"
        )

    parent = _load_yaml(parent_path)
    if parent.get("extends"):
        raise ValueError(
            f"{config_path.name} extends {parent_id}, which itself extends "
            f"{parent['extends']}. Inheritance is single-level only."
        )

    if parent.get("schema_version") != config.get("schema_version"):
        raise ValueError(
            f"{config_path.name} schema_version {config.get('schema_version')} "
            f"does not match parent {parent_path.name} "
            f"schema_version {parent.get('schema_version')}"
        )

    merged = _deep_merge(parent, config)
    merged.pop("extends", None)
    return merged
```

- [ ] **Step 4: Run all render tests**

```bash
cd /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent && /Users/sarahnovotny/Github/python3.12-venv/bin/pytest tests/test_render.py -v
```

Expected: 8 passed (4 prior + 4 new).

- [ ] **Step 5: Commit**

```bash
git add scripts/agent/render.py scripts/agent/tests/test_render.py
git commit -m "$(cat <<'EOF'
feat(scripts/agent): config extends resolver in render.py

resolve_config() implements single-level inheritance per DESIGN.md §6:
deep-merge object fields, fully replace arrays, override scalars, null
clears, schema_version must match. Raises FileNotFoundError when extends
points at a missing file and ValueError on chains longer than one hop.

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 10: `render.py` — claude-code target (basic stitch)

**Files:**
- Modify: `scripts/agent/render.py`
- Modify: `scripts/agent/tests/test_render.py`

- [ ] **Step 1: Write a failing test for claude-code render**

Append to `tests/test_render.py`:

```python
def test_claude_code_render_produces_skill_md(tmp_path: Path):
    """Render writes a SKILL.md with the manifest's frontmatter and SKILL.md body."""
    import render as r

    skill_src = tmp_path / "src" / "demo-skill"
    skill_src.mkdir(parents=True)
    (skill_src / "manifest.yaml").write_text(
        "schema_version: 1\n"
        "name: demo-skill\n"
        "description: A demo skill.\n"
        "version: 0.1.0\n"
        "governance: { license: CC-BY-4.0, ai_attribution: 'foo' }\n"
        "arguments: []\n"
        "dependencies:\n"
        "  tools:\n"
        "    - { id: filesystem, required: true, capabilities: [read] }\n"
        "output: { primary: { type: markdown, location: out/x.md } }\n"
        "boundaries: { does_not: ['nothing'] }\n"
        "failure_modes:\n"
        "  - { condition: x, action: y }\n"
        "narrative: SKILL.md\n"
    )
    (skill_src / "SKILL.md").write_text("# Body\n\nProse.\n")

    out = tmp_path / "out"
    r.render_claude_code(skill_src, out, symlink=False)

    rendered = (out / "demo-skill" / "SKILL.md").read_text()
    assert rendered.startswith("---\n")
    assert "name: demo-skill" in rendered
    assert "description: A demo skill" in rendered
    assert "Skill Contract" in rendered  # manifest-context block
    assert "Prose." in rendered
```

- [ ] **Step 2: Run test — expect failure**

```bash
cd /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent && /Users/sarahnovotny/Github/python3.12-venv/bin/pytest tests/test_render.py::test_claude_code_render_produces_skill_md -v
```

Expected: AttributeError on `r.render_claude_code`.

- [ ] **Step 3: Add `render_claude_code` to `render.py`**

After `resolve_config()`, add:

```python
def _claude_code_frontmatter(manifest: dict[str, Any]) -> str:
    """Build the YAML frontmatter Claude Code requires."""
    description = " ".join(manifest["description"].split())  # collapse whitespace to single line
    return (
        "---\n"
        f"name: {manifest['name']}\n"
        f"description: {description}\n"
        "---\n"
    )


def _manifest_context_block(manifest: dict[str, Any]) -> str:
    """Build the auto-generated 'Skill Contract' block injected into rendered SKILL.md."""
    summary = {
        k: manifest[k]
        for k in ("arguments", "dependencies", "composition", "output", "boundaries")
        if k in manifest
    }
    yaml_text = yaml.safe_dump(summary, sort_keys=False)
    return (
        "## Skill Contract (auto-generated from manifest.yaml; do not edit)\n\n"
        "```yaml\n"
        f"{yaml_text}"
        "```\n\n"
        "See `scripts/agent/<skill>/manifest.yaml` for canonical.\n\n"
    )


def render_claude_code(skill_dir: Path, output_dir: Path, *, symlink: bool = True) -> Path:
    """Render a skill for Claude Code. Returns the path of the written SKILL.md."""
    manifest = _load_manifest(skill_dir)
    errors = _validate_manifest(manifest)
    if errors:
        raise ValueError(f"manifest validation failed for {skill_dir.name}: {errors}")

    skill_body_path = skill_dir / manifest.get("narrative", "SKILL.md")
    skill_body = skill_body_path.read_text()

    rendered = (
        _claude_code_frontmatter(manifest)
        + "\n"
        + _manifest_context_block(manifest)
        + skill_body
    )

    target_dir = output_dir / manifest["name"]
    target_dir.mkdir(parents=True, exist_ok=True)
    target_skill = target_dir / "SKILL.md"
    # Atomic write
    tmp = target_skill.with_suffix(".tmp")
    tmp.write_text(rendered)
    tmp.replace(target_skill)

    return target_skill
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent && /Users/sarahnovotny/Github/python3.12-venv/bin/pytest tests/test_render.py -v
```

Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/agent/render.py scripts/agent/tests/test_render.py
git commit -m "$(cat <<'EOF'
feat(scripts/agent): claude-code target in render.py (basic stitch)

render_claude_code() loads + validates a manifest, builds Claude Code
frontmatter (name + description), injects an auto-generated Skill
Contract block summarising the manifest's structured fields, then
appends the SKILL.md body verbatim. Atomic write via tempfile + rename.

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 11: `render.py` — install side-effects (symlink/copy + sibling files)

**Files:**
- Modify: `scripts/agent/render.py`
- Modify: `scripts/agent/tests/test_render.py`

- [ ] **Step 1: Write failing tests for install behaviour**

Append to `tests/test_render.py`:

```python
def test_claude_code_render_with_symlink(tmp_path: Path):
    """--symlink (default): destination SKILL.md is a symlink resolving back into the source tree."""
    import render as r

    skill_src = tmp_path / "src" / "demo-skill"
    skill_src.mkdir(parents=True)
    (skill_src / "manifest.yaml").write_text(MINIMAL_MANIFEST)
    (skill_src / "SKILL.md").write_text("# Body\n")

    out = tmp_path / "out"
    target = r.render_claude_code(skill_src, out, symlink=True)

    # In symlink mode, render writes to a staging path within the source dir
    # then symlinks it from the destination.
    assert target.is_symlink() or (out / "demo-skill" / "SKILL.md").is_symlink()


def test_claude_code_render_copies_sibling_files(tmp_path: Path):
    """Sibling files declared in the manifest's runtime_role: input data deps are copied/symlinked alongside."""
    import render as r

    skill_src = tmp_path / "src" / "demo-skill"
    skill_src.mkdir(parents=True)
    manifest_with_sibling = (
        "schema_version: 1\n"
        "name: demo-skill\n"
        "description: Demo with sibling.\n"
        "version: 0.1.0\n"
        "governance: { license: CC-BY-4.0, ai_attribution: 'foo' }\n"
        "arguments: []\n"
        "dependencies:\n"
        "  tools:\n"
        "    - { id: filesystem, required: true, capabilities: [read] }\n"
        "  data:\n"
        "    - path: data.json\n"
        "      access: read\n"
        "      runtime_role: input\n"
        "      provisioning: { kind: in-repo, tracked_in_repo: true }\n"
        "output: { primary: { type: markdown, location: out/x.md } }\n"
        "boundaries: { does_not: ['nothing'] }\n"
        "failure_modes:\n"
        "  - { condition: x, action: y }\n"
        "narrative: SKILL.md\n"
    )
    (skill_src / "manifest.yaml").write_text(manifest_with_sibling)
    (skill_src / "SKILL.md").write_text("# Body\n")
    (skill_src / "data.json").write_text("{}")

    out = tmp_path / "out"
    r.render_claude_code(skill_src, out, symlink=False)
    assert (out / "demo-skill" / "data.json").exists()
```

Add the `MINIMAL_MANIFEST` constant near the top of `test_render.py` (after imports):

```python
MINIMAL_MANIFEST = (
    "schema_version: 1\n"
    "name: demo-skill\n"
    "description: A demo skill.\n"
    "version: 0.1.0\n"
    "governance: { license: CC-BY-4.0, ai_attribution: 'foo' }\n"
    "arguments: []\n"
    "dependencies:\n"
    "  tools:\n"
    "    - { id: filesystem, required: true, capabilities: [read] }\n"
    "output: { primary: { type: markdown, location: out/x.md } }\n"
    "boundaries: { does_not: ['nothing'] }\n"
    "failure_modes:\n"
    "  - { condition: x, action: y }\n"
    "narrative: SKILL.md\n"
)
```

- [ ] **Step 2: Run tests — expect failures**

Both new tests fail (no symlink behaviour yet, no sibling-file copy).

- [ ] **Step 3: Update `render_claude_code` in `render.py` for symlink + sibling-file install**

Replace the body of `render_claude_code` with:

```python
def render_claude_code(skill_dir: Path, output_dir: Path, *, symlink: bool = True) -> Path:
    """Render a skill for Claude Code. Returns the path of the written SKILL.md."""
    manifest = _load_manifest(skill_dir)
    errors = _validate_manifest(manifest)
    if errors:
        raise ValueError(f"manifest validation failed for {skill_dir.name}: {errors}")

    skill_body_path = skill_dir / manifest.get("narrative", "SKILL.md")
    skill_body = skill_body_path.read_text()

    rendered = (
        _claude_code_frontmatter(manifest)
        + "\n"
        + _manifest_context_block(manifest)
        + skill_body
    )

    target_dir = output_dir / manifest["name"]
    target_dir.mkdir(parents=True, exist_ok=True)
    target_skill = target_dir / "SKILL.md"

    if symlink:
        # Write the rendered SKILL.md to a staging file in the source tree
        # and symlink it from the destination so source-tree edits to the
        # manifest get picked up on next render and live SKILL.md edits
        # are visible immediately.
        staging = skill_dir / ".rendered.SKILL.md"
        tmp = staging.with_suffix(".tmp")
        tmp.write_text(rendered)
        tmp.replace(staging)
        if target_skill.exists() or target_skill.is_symlink():
            target_skill.unlink()
        target_skill.symlink_to(staging.resolve())
    else:
        # Copy mode: atomic write to the destination.
        tmp = target_skill.with_suffix(".tmp")
        tmp.write_text(rendered)
        tmp.replace(target_skill)

    # Sibling files: any data dep with runtime_role: input and a relative path
    # that resolves to an in-repo file gets installed alongside SKILL.md.
    deps = manifest.get("dependencies", {})
    for data_dep in deps.get("data", []) or []:
        if data_dep.get("runtime_role") != "input":
            continue
        prov = data_dep.get("provisioning", {})
        if not prov.get("tracked_in_repo"):
            continue
        rel_path = data_dep.get("path", "")
        if "/" in rel_path or rel_path.startswith("{"):
            # Path templates or repo-rooted paths aren't sibling files.
            continue
        src = skill_dir / rel_path
        if not src.exists():
            continue
        dest = target_dir / rel_path
        if dest.exists() or dest.is_symlink():
            dest.unlink()
        if symlink:
            dest.symlink_to(src.resolve())
        else:
            tmp = dest.with_suffix(dest.suffix + ".tmp")
            tmp.write_bytes(src.read_bytes())
            tmp.replace(dest)

    return target_skill
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent && /Users/sarahnovotny/Github/python3.12-venv/bin/pytest tests/test_render.py -v
```

Expected: 11 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/agent/render.py scripts/agent/tests/test_render.py
git commit -m "$(cat <<'EOF'
feat(scripts/agent): symlink/copy install + sibling-file placement

render_claude_code() now supports --symlink (default) and --copy modes.
Symlink mode writes a .rendered.SKILL.md staging file in the source tree
and links it from the destination so live edits propagate. Sibling files
declared as data deps with runtime_role: input + tracked_in_repo: true
are installed alongside (e.g. triage_milestones.json).

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 12: `render.py` — wire CLI dispatch + path substitution

**Files:**
- Modify: `scripts/agent/render.py`
- Modify: `scripts/agent/tests/test_render.py`

- [ ] **Step 1: Write a failing CLI integration test**

Append to `tests/test_render.py`:

```python
def test_cli_dispatch_to_claude_code(tmp_path: Path):
    """Running render.py <skill> --target=claude-code --output=<path> --copy works end-to-end."""
    # Use a temp skill set up exactly like a real one in scripts/agent/.
    skill_src = REPO_ROOT / "scripts" / "agent" / "_test_demo_skill"
    skill_src.mkdir(parents=True, exist_ok=True)
    try:
        (skill_src / "manifest.yaml").write_text(MINIMAL_MANIFEST.replace("demo-skill", "_test_demo_skill"))
        (skill_src / "SKILL.md").write_text("# Hello\n")

        out = tmp_path / "out"
        result = run_render(
            "_test_demo_skill",
            "--target=claude-code",
            "--copy",
            f"--output={out}",
        )
        assert result.returncode == 0, result.stderr
        rendered = (out / "_test_demo_skill" / "SKILL.md").read_text()
        assert "name: _test_demo_skill" in rendered
        assert "Hello" in rendered
    finally:
        # Cleanup
        for f in skill_src.iterdir():
            f.unlink()
        skill_src.rmdir()


def test_path_substitution_replaces_repo_root(tmp_path: Path):
    """<repo_root> placeholders in SKILL.md are substituted with the absolute repo path."""
    import render as r

    skill_src = tmp_path / "src" / "demo-skill"
    skill_src.mkdir(parents=True)
    (skill_src / "manifest.yaml").write_text(MINIMAL_MANIFEST)
    (skill_src / "SKILL.md").write_text(
        "# Body\nConfigs live at <repo_root>/scripts/agent/configs/.\n"
    )

    out = tmp_path / "out"
    # Simulate a known repo root for substitution.
    r.render_claude_code(skill_src, out, symlink=False, repo_root=Path("/abs/repo"))

    rendered = (out / "demo-skill" / "SKILL.md").read_text()
    assert "/abs/repo/scripts/agent/configs/" in rendered
    assert "<repo_root>" not in rendered
```

- [ ] **Step 2: Run tests — expect failures**

```bash
cd /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent && /Users/sarahnovotny/Github/python3.12-venv/bin/pytest tests/test_render.py::test_cli_dispatch_to_claude_code tests/test_render.py::test_path_substitution_replaces_repo_root -v
```

Expected: failures (CLI dispatch is still a stub; render_claude_code doesn't accept repo_root).

- [ ] **Step 3: Update `render_claude_code` to accept `repo_root` and substitute**

Modify the signature and body of `render_claude_code`:

```python
def render_claude_code(
    skill_dir: Path,
    output_dir: Path,
    *,
    symlink: bool = True,
    repo_root: Path | None = None,
) -> Path:
    """Render a skill for Claude Code. Returns the path of the written SKILL.md."""
    manifest = _load_manifest(skill_dir)
    errors = _validate_manifest(manifest)
    if errors:
        raise ValueError(f"manifest validation failed for {skill_dir.name}: {errors}")

    skill_body_path = skill_dir / manifest.get("narrative", "SKILL.md")
    skill_body = skill_body_path.read_text()

    # Render-time path substitution: replace <repo_root> with the absolute repo path.
    if repo_root is None:
        repo_root = REPO_ROOT
    skill_body = skill_body.replace("<repo_root>", str(repo_root))

    rendered = (
        _claude_code_frontmatter(manifest)
        + "\n"
        + _manifest_context_block(manifest)
        + skill_body
    )

    # ... existing target_dir + symlink/copy logic unchanged ...
```

(Keep the rest of the function body the same as Task 11.)

- [ ] **Step 4: Wire CLI dispatch in `main()`**

Replace the body of `main()`:

```python
def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.validate_all:
        return _cmd_validate_all()

    if not args.skill:
        parser.error("the following arguments are required: skill (or use --validate-all)")

    if args.target == "generic":
        print("Generic-prompt rendering deferred to v2; CLI accepts the flag for forward-compat.", file=sys.stderr)
        manifest = _load_manifest(AGENT_DIR / args.skill)
        print(yaml.safe_dump({k: manifest.get(k) for k in ("name", "version", "arguments")}, sort_keys=False), file=sys.stderr)
        return 2

    skill_dir = AGENT_DIR / args.skill
    if not skill_dir.exists():
        print(f"render.py: skill {args.skill!r} not found at {skill_dir}", file=sys.stderr)
        return 1

    output_dir = Path(args.output) if args.output else Path.home() / ".claude" / "skills"

    if args.dry_run:
        print(f"DRY RUN: would render {args.skill} -> {output_dir / args.skill}", file=sys.stderr)
        manifest = _load_manifest(skill_dir)
        errors = _validate_manifest(manifest)
        if errors:
            print(f"Manifest validation failures: {errors}", file=sys.stderr)
            return 1
        return 0

    target_path = render_claude_code(skill_dir, output_dir, symlink=args.symlink)
    print(f"Rendered {args.skill} -> {target_path}", file=sys.stderr)

    # Out-of-band data deps reminder
    manifest = _load_manifest(skill_dir)
    for data_dep in manifest.get("dependencies", {}).get("data", []) or []:
        if data_dep.get("provisioning", {}).get("kind") == "out-of-band":
            populated_by = data_dep.get("provisioning", {}).get("populated_by", {})
            tool = populated_by.get("tool", "(unknown)")
            print(f"Reminder: data path {data_dep['path']} is populated out-of-band by {tool}", file=sys.stderr)

    return 0
```

- [ ] **Step 5: Run all render tests**

```bash
cd /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent && /Users/sarahnovotny/Github/python3.12-venv/bin/pytest tests/test_render.py -v
```

Expected: 13 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/agent/render.py scripts/agent/tests/test_render.py
git commit -m "$(cat <<'EOF'
feat(scripts/agent): wire CLI dispatch + render-time path substitution

main() now dispatches to render_claude_code() with --output (default
~/.claude/skills/), --symlink/--copy, --dry-run. <repo_root> in SKILL.md
is substituted with the absolute repo path at render time so the
running model can locate configs without knowing where the repo lives.
--target=generic emits a "deferred to v2" notice and exits 2. Out-of-band
data deps trigger a post-render reminder.

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 13: Write `configs/ws4.yaml` (worked workstream config)

**Files:**
- Create: `scripts/agent/configs/ws4.yaml`

- [ ] **Step 1: Write `scripts/agent/configs/ws4.yaml`**

```yaml
schema_version: 1
workstream:
  id: ws4
  name: WS4
  full_name: Workstream 4 — Secure Design Patterns for Agentic Systems
  parent_workstream: null

repo:
  owner: cosai-oasis
  name: ws4-secure-design-agentic-systems

leads:
  - { name: Sarah Novotny, github: sarahnovotny, role: chair }
  - { name: Ian Molloy, github: imolloy, role: chair }
  - { name: Alex Polyakov, github: AIRedTeaming, role: supporting }
  - { name: Raghuram Yeluri, github: null, role: supporting }

meeting:
  cadence: Thursdays
  time: "12:00 ET / 09:00 PT"
  meeting_minutes_dir: meeting_minutes/ws4
  filename_pattern: "WS4-{YYYYMMDD}.md"
  agenda_template_discussion: 84
  agenda_section_template: standard
  fallback_minutes_dir: null

channels:
  slack:
    workspace: cosai-op
    channel: ws4-secure-design-agentic-systems
  mailing_list: cosai-agentic-systems-ws@lists.oasis-open-projects.org

triage:
  milestones_file: ../cosai-issue-triage/triage_milestones.json
  milestone_namespace: ws4
  recognised_triage_labels:
    - review
    - accepted
    - whitepaper
    - playbook
    - v2 branch
  chair_label_authority: true
```

- [ ] **Step 2: Validate via `--validate-all`**

```bash
/Users/sarahnovotny/Github/python3.12-venv/bin/python3 /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent/render.py --validate-all
```

Expected: prints `OK   configs/ws4.yaml` and exits 0.

- [ ] **Step 3: Commit**

```bash
git add scripts/agent/configs/ws4.yaml
git commit -m "$(cat <<'EOF'
feat(scripts/agent/configs): add ws4.yaml — WS4 workstream config

Top-level workstream config (no extends). Carries repo, leads, meeting,
channels, triage. Validates against _config.schema.json via
render.py --validate-all.

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 14: Migrate `cosai-meeting-agenda` — manifest.yaml

**Files:**
- Create: `scripts/agent/cosai-meeting-agenda/manifest.yaml`

- [ ] **Step 1: Write `scripts/agent/cosai-meeting-agenda/manifest.yaml`**

Copy the worked example from DESIGN.md §5 verbatim:

```yaml
schema_version: 1
name: cosai-meeting-agenda
description: |
  Generate a structured meeting agenda for a CoSAI workstream or SIG by pulling
  from meeting minutes, GitHub issues, and PRs. Produces a draft for human
  review before promotion to a GitHub Discussion.
version: 1.0.0

governance:
  license: CC-BY-4.0
  ai_attribution: |
    AI-assisted commits use:
    Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
    Per CoSAI vendor-neutral attribution convention from
    cosai-oasis/secure-ai-tooling#149.

arguments:
  - name: workstream
    type: string
    required: true
    description: |
      Workstream/SIG slug matching a file in scripts/agent/configs/.
      Examples: ws4, ws3, adlc, rm-sig, code-sig.

dependencies:
  tools:
    - id: gh
      purpose: Read issues, PRs, discussions
      required: true
      capabilities: [read]
    - id: filesystem
      purpose: Read meeting_minutes/<ws>/, write agenda_drafts/<ws>/
      required: true
      capabilities: [read, write]
  configs:
    - path: configs/{workstream}.yaml
      schema: configs/_config.schema.json
  data:
    - path: "{config.meeting.meeting_minutes_dir}/"
      access: read
      runtime_role: input
      provisioning:
        kind: out-of-band
        tracked_in_repo: false
        populated_by:
          tool: scripts/fetch_meeting_minutes.py
          repo: cosai-oasis/ws4-secure-design-agentic-systems
          documented_at: scripts/README.md
        cadence: |
          User-managed; typically run nightly via cron or manually before
          generating an agenda.
        on_missing: |
          Halt and instruct the user to run scripts/fetch_meeting_minutes.py
          (with --skip-existing for incremental). Do not silently fall back
          to fetching from Drive directly.
    - path: "agenda_drafts/{workstream}/"
      access: write
      runtime_role: output
      provisioning:
        kind: in-repo
        tracked_in_repo: true

composition:
  calls:
    - skill: cosai-issue-triage
      mode: optional
      condition: |
        An issue surfaced for the agenda lacks any of the recognised triage
        labels listed in config.triage.recognised_triage_labels. v1 status:
        deferred — declared in the contract for forward-compat.
      passes:
        issue_number: "<issue.number>"
        workstream: "<argument.workstream>"
      receives:
        triage_note: markdown
        suggested_labels: array
        suggested_milestone: string
  called_by: []

output:
  primary:
    type: markdown
    location: agenda_drafts/{workstream}/{meeting_date}.md
    frontmatter:
      schema_version: int
      workstream: string
      meeting_date: date
      generated_at: timestamp
      generated_by: string
      generated_by_role: enum
      source_skill: string
      source_skill_version: semver
      status: enum
      promoted_to: string
      promoted_at: timestamp
      supersedes: string
  side_effects:
    - kind: github-discussion
      condition: user explicitly approves promotion
      action: |
        Create discussion in {config.repo} matching the agenda template.
        Update draft frontmatter with promoted_to + promoted_at.
    - kind: github-issue-update
      condition: |
        Phase 3 composition only; chair-permission-gated; explicit per-issue
        approval. v1 of this skill does NOT touch issues.
      action: |
        Post triage comment + apply labels + set milestone (chair) or
        post comment with cc to chairs (non-chair).
      v1_status: deferred

boundaries:
  does_not:
    - Post to a GitHub Discussion without explicit user approval
    - Apply labels, set milestones, or close issues (v1 — deferred to Phase 3)
    - Modify meeting_minutes/ (read-only)
    - Touch other workstreams' configs (single-workstream invocation)

failure_modes:
  - condition: meeting_minutes/<workstream>/ missing or empty
    action: |
      Halt with the exact directory path expected. If
      config.meeting.fallback_minutes_dir is set, scan that directory for
      <workstream>-tagged context and proceed with a "minutes-sparse" notice
      in the agenda. See dependencies.data[0].provisioning.on_missing for
      the canonical recovery instruction.
  - condition: gh CLI unavailable or unauthenticated
    action: |
      Halt with auth instructions. Do not silently fall back to web fetch.
  - condition: previous-agenda discussion not found
    action: |
      Proceed; mark "Action Item Follow-ups" with a note explaining no prior
      agenda was found.

narrative: SKILL.md
```

- [ ] **Step 2: Validate**

```bash
/Users/sarahnovotny/Github/python3.12-venv/bin/python3 /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent/render.py --validate-all
```

Expected: `OK   cosai-meeting-agenda/manifest.yaml`.

- [ ] **Step 3: Commit (defer until SKILL.md is in place — Task 15)**

Hold the commit until Task 15 so the skill directory is committed as a unit.

---

## Task 15: Migrate `cosai-meeting-agenda` — SKILL.md

**Files:**
- Create: `scripts/agent/cosai-meeting-agenda/SKILL.md`

The new SKILL.md is the existing `agenda` SKILL.md with WS4-specific values replaced by `{config.X}` references.

- [ ] **Step 1: Read the source**

```bash
/usr/bin/cat /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/.claude/skills.bak/agenda/SKILL.md
```

Note the WS4 specifics:
- "Thursdays 12:00 ET" — hardcoded
- "Wednesdays 11:00 ET" — ADLC hardcoded
- Discussion #84 reference
- `meeting_minutes/` and `meeting_minutes/adlc/` — paths
- WS4 leads, ADLC leads — names
- MemPalace drawer ID

- [ ] **Step 2: Write `scripts/agent/cosai-meeting-agenda/SKILL.md`**

Use the source SKILL.md but with these replacements:

| Original | Replacement |
|---|---|
| `WS4 / ADLC Meeting Agenda Generator` | `CoSAI Meeting Agenda Generator` |
| The "Argument" section's hardcoded WS4/ADLC table | A note that argument is `workstream` (a slug from `<repo_root>/scripts/agent/configs/`) |
| `Thursdays 12:00 ET` / `Wednesdays 11:00 ET` | `{config.meeting.cadence} {config.meeting.time}` |
| `meeting_minutes/` / `meeting_minutes/adlc/` | `{config.meeting.meeting_minutes_dir}/` |
| The Discussion #84 paragraph | `The authoritative format is the discussion referenced in {config.meeting.agenda_template_discussion} (a GitHub Discussion number in {config.repo}). When in doubt, fetch that discussion and match its style.` |
| WS4 lead names (Sarah Novotny, Ian Molloy, Alex Polyakov, Raghuram Yeluri) | `{config.leads}` |
| ADLC SIG leads (Kathleen Goeschel, Parul Singh) | (delete; this is now config-driven) |
| `meeting_minutes fetched nightly from Google Drive by ~/Github/scripts/fetch_meeting_minutes.py` | `meeting_minutes/<workstream>/ is populated out-of-band by scripts/fetch_meeting_minutes.py — see this skill's manifest.yaml dependencies.data[0].provisioning for details.` |
| MemPalace drawer ID | (delete or leave with a note that this was the original decision drawer) |

The full content is below. Use this verbatim.

```markdown
---
name: cosai-meeting-agenda
description: Generate a structured meeting agenda for a CoSAI workstream or SIG by pulling from meeting minutes, GitHub issues, and PRs. Produces a draft for human review before promotion to a GitHub Discussion.
---

# CoSAI Meeting Agenda Generator

Generate a structured agenda for an upcoming CoSAI workstream or SIG meeting by pulling from meeting minutes, GitHub issues, and PRs. The output is a draft for human review, written to `agenda_drafts/{workstream}/{meeting_date}.md`. Promotion to a GitHub Discussion requires explicit user approval.

## Argument

Single argument: `workstream` — a slug naming a file in `<repo_root>/scripts/agent/configs/<slug>.yaml`. The skill loads that config and uses it to resolve repo, leads, meeting cadence, minutes directory, recognised triage labels, etc. If omitted, ask the user which workstream.

## Canonical template

The authoritative format is the GitHub Discussion in `{config.repo.owner}/{config.repo.name}` whose number is `{config.meeting.agenda_template_discussion}`. When in doubt, fetch that discussion and match its style.

## Configuration loading

At run time:

1. Read the workstream config: `<repo_root>/scripts/agent/configs/{workstream}.yaml` (auto-resolved by the renderer at install time).
2. If the config has `extends:`, the renderer's resolution logic merges with the parent (single-level only). For an interactive read, you can verify by running `<repo_root>/scripts/agent/render.py --validate-all` — it prints the effective config.
3. Use `{config.X}` references throughout this document — replace with the resolved value at run time.

## Process

1. **Fetch the previous agenda.** Look for the most recent agenda Discussion in `{config.repo.owner}/{config.repo.name}` matching the convention from `{config.meeting.agenda_template_discussion}`. Extract its open action items — these carry into the new agenda's Action Item Follow-ups unless visibly resolved.

2. **Read recent meeting minutes** from `{config.meeting.meeting_minutes_dir}` (last 2-3 files, sorted by date). Extract:
   - New action items and their owners (from the most recent meeting)
   - Resolutions of prior action items
   - Decisions made
   - Topics deferred to future meetings
   - If `{config.meeting.fallback_minutes_dir}` is set and the primary directory is sparse or empty, also scan the fallback directory for `{workstream}`-related context.

   `{config.meeting.meeting_minutes_dir}` is populated out-of-band by `scripts/fetch_meeting_minutes.py` — see this skill's `manifest.yaml` `dependencies.data[0].provisioning` for the canonical sync source. If the directory is missing, halt and instruct the user to run the fetch script.

3. **Pull open PRs** from `{config.repo.owner}/{config.repo.name}`:
   - Group by: contributor PRs needing review vs external submissions needing triage
   - Highlight PRs aligned with this workstream's focus areas (specific to the config; chairs to interpret)

4. **Pull open issues**:
   - RFCs under review (label: `review`)
   - Issues awaiting consensus vote
   - Unlabeled issues needing triage
   - New issues since last meeting

   For unlabeled issues, the v1 of this skill notes them in the agenda with a `(needs triage)` annotation. The Phase 3 composition (deferred) will invoke `cosai-issue-triage` inline and embed the triage note in the agenda; for v1, simply list the issue.

5. **Check for cross-meeting updates** — note any sibling SIGs or parent workstream items that affect the current workstream's agenda. The config's `workstream.parent_workstream` and `meeting.fallback_minutes_dir` give pointers.

6. **Format the agenda** using the structure below. Do **not** include a disclaimer.

```markdown
## {config.workstream.name} Agenda — {meeting_date_human}

### 1. Action Item Follow-ups

| Owner | Action | Status |
|-------|--------|--------|
| ...   | ...    | Done / Done → #NN / Done → PR #NN / Done — <note> / ? / In progress |

### 2. PRs Needing Review

| PR | Author | Notes |
|----|--------|-------|
| **#NN** | ... | ... |

### 3. Issues Needing Chair Decision

**Formal call for consensus (if scheduled):**

| Issue | Title | Author |
|-------|-------|--------|
| **#NN** | ... | ... |

**RFCs under review:**

| Issue | Title | Notes |
|-------|-------|-------|
| **#NN** | ... | ... |

**Unlabeled issues needing triage:**

| Issue | Title |
|-------|-------|
| **#NN** | ... |

### 4. New Issues Since Last Meeting

| Issue | Title | Notes |
|-------|-------|-------|
| **#NN** | ... | ... |

### 5. Cross-Stream Updates

| Topic | Status |
|-------|--------|
| ...   | ...    |
```

**Formatting rules:**
- **Lean tables over bullets.** Only fall back to bullets when content genuinely doesn't fit a 2-3-column table.
- Use `**#NN**` (bold) for issue/PR numbers in tables.

**Action Item Follow-ups rules:**
- Merge (a) open items from the previous agenda and (b) new action items from the most recent meeting minutes into a single table.
- Mark items visibly completed as **Done** with a pointer: `Done → #69`, `Done → PR #68`, `Done — delivered 4/16`.
- Done items **stay on the current agenda** for visibility and drop off the following week.
- For items carried across multiple meetings, note the carry (`? (carried from Apr 9 & Apr 16)`).
- For ambiguous items, annotate inline rather than silently resolving — flag for live clarification.

7. **Write the draft to `<repo_root>/agenda_drafts/{workstream}/{meeting_date}.md`.** Frontmatter per the contract in DESIGN.md §7. The fields `generated_at`, `generated_by` (gh identity), `generated_by_role` (looked up from `{config.leads}` plus a `gh` permission check) are populated automatically.

8. **Present to user for review** before promotion to a GitHub Discussion. Never post without approval.

## Determining "last meeting"

Meeting files are named per `{config.meeting.filename_pattern}` in `{config.meeting.meeting_minutes_dir}`. Use the most recent file's date as the last meeting date. Issues and PRs created or updated after that date are "new since last meeting." If the directory has no files, fall back to `{config.meeting.fallback_minutes_dir}` (if set) and note the sparse-minutes condition in the agenda.

## Key context

- Repo: `{config.repo.owner}/{config.repo.name}`
- Meeting cadence: `{config.meeting.cadence}` at `{config.meeting.time}`
- Meeting minutes directory: `{config.meeting.meeting_minutes_dir}`
- Workstream leads: `{config.leads}` (chairs are the subset with `role: chair`)
- Slack: `#{config.channels.slack.channel}` in `{config.channels.slack.workspace}`
- Mailing list: `{config.channels.mailing_list}`
- Today's date: must come from the environment, not be guessed.
```

- [ ] **Step 3: Validate the manifest+SKILL.md combo via dry-run**

```bash
/Users/sarahnovotny/Github/python3.12-venv/bin/python3 /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent/render.py cosai-meeting-agenda --target=claude-code --dry-run
```

Expected: `DRY RUN: would render cosai-meeting-agenda -> ...` and exit 0.

- [ ] **Step 4: Commit the migration as a unit (manifest + SKILL.md)**

```bash
git add scripts/agent/cosai-meeting-agenda/
git commit -m "$(cat <<'EOF'
feat(scripts/agent): migrate agenda skill to cosai-meeting-agenda/

Splits the existing .claude/skills.bak/agenda/SKILL.md into:
- manifest.yaml: structured contracts (dependencies, output, boundaries,
  failure_modes, governance, composition).
- SKILL.md: imperative process narrative, with WS4 specifics replaced
  by {config.X} references resolved at run time from
  configs/<workstream>.yaml.

Hardcoded WS4/ADLC values (cadence, leads, Discussion #84, paths) move
to the config file. The skill is now workstream-agnostic — adding a
new workstream means dropping a config file, not editing this skill.

Phase 3 composition (calling cosai-issue-triage inline for unlabeled
issues) is declared in the manifest's composition.calls block but not
implemented in v1; agenda flags unlabeled issues with `(needs triage)`.

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 16: Migrate `cosai-issue-triage` — manifest.yaml

**Files:**
- Create: `scripts/agent/cosai-issue-triage/manifest.yaml`

- [ ] **Step 1: Write `scripts/agent/cosai-issue-triage/manifest.yaml`**

```yaml
schema_version: 1
name: cosai-issue-triage
description: |
  Produce a structured triage note for a GitHub issue or PR in a CoSAI
  workstream's repo, matching the format established by @parmarmanojkumar.
  Output is a draft for human review; never posts without approval.
version: 1.0.0

governance:
  license: CC-BY-4.0
  ai_attribution: |
    AI-assisted commits use:
    Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
    Per CoSAI vendor-neutral attribution convention from
    cosai-oasis/secure-ai-tooling#149.

arguments:
  - name: workstream
    type: string
    required: true
    description: |
      Workstream/SIG slug matching a file in scripts/agent/configs/.
  - name: issue_number
    type: integer
    required: true
    description: GitHub issue or PR number to triage.

dependencies:
  tools:
    - id: gh
      purpose: Read issue/PR; optionally post comment if user approves.
      required: true
      capabilities: [read]
    - id: filesystem
      purpose: Read configs and milestones file.
      required: true
      capabilities: [read]
  configs:
    - path: configs/{workstream}.yaml
      schema: configs/_config.schema.json
  data:
    - path: triage_milestones.json
      access: read
      runtime_role: input
      provisioning:
        kind: in-repo
        tracked_in_repo: true

composition:
  calls: []
  called_by:
    - skill: cosai-meeting-agenda
      mode: optional
      condition: |
        Agenda flow finds an unlabeled issue and wants an inline triage note.
        v1 status: deferred — declared for forward-compat.

output:
  primary:
    type: markdown
    location: chat
  side_effects:
    - kind: github-issue-comment
      condition: user explicitly approves posting
      action: Post the triage note as a comment on the issue.
    - kind: github-issue-labels
      condition: |
        Runtime gh permission check shows the user has chair-level write
        access AND user explicitly approves. Otherwise, the comment includes
        proposed labels with cc to chairs for action.
      action: Apply labels and set milestone derived from triage_milestones.json.
      v1_status: deferred

boundaries:
  does_not:
    - Post a comment without explicit user approval
    - Apply labels or set milestones in v1 (Phase 3 deferred)
    - Modify the issue body or close the issue
    - Operate across workstreams in a single invocation

failure_modes:
  - condition: issue not found in {config.repo}
    action: |
      Halt with the exact `gh` command attempted and the response body.
  - condition: triage_milestones.json missing the requested namespace
    action: |
      Halt; print the available namespaces and ask the user to either
      (a) add the namespace to triage_milestones.json or (b) re-invoke
      with a different workstream slug.
  - condition: gh CLI unavailable or unauthenticated
    action: Halt with auth instructions.

narrative: SKILL.md
```

- [ ] **Step 2: Validate**

Continue without running `--validate-all` yet — `triage_milestones.json` doesn't exist. Will run after Task 17.

---

## Task 17: Migrate `triage_metadata.json` to `triage_milestones.json`

**Files:**
- Create: `scripts/agent/cosai-issue-triage/triage_milestones.json`

The existing `triage_metadata.json` is a flat array. The new file wraps it in `{ "namespaces": { "ws4": { "milestones": [...] } } }`.

- [ ] **Step 1: Write `scripts/agent/cosai-issue-triage/triage_milestones.json`**

```json
{
  "schema_version": 1,
  "namespaces": {
    "ws4": {
      "milestones": [
        {
          "wave": "Wave 1 editorial",
          "milestone": "mcp-security-whitepaper-v1.1-editorial",
          "contents": "Low-risk doc fixes for a v1.1 cut"
        },
        {
          "wave": "Wave 1 docs support",
          "milestone": "docs-support-v1.0",
          "contents": "Diagrams, reference artifacts supporting the whitepaper"
        },
        {
          "wave": "Wave 2 conceptual",
          "milestone": "mcp-security-whitepaper-v1.2-conceptual",
          "contents": "Substantive v2 whitepaper content"
        },
        {
          "wave": "Playbook wave 1",
          "milestone": "playbook-v1.0",
          "contents": "The 7 playbooks (#52-#58)"
        },
        {
          "wave": "Program tracking",
          "milestone": "playbook-v1.0-program",
          "contents": "Umbrella/EPIC for the playbook program"
        },
        {
          "wave": "Later conceptual track",
          "milestone": "identity-delegation-v1.0",
          "contents": "Delegation semantics, token binding, portable identity"
        },
        {
          "wave": "Later conceptual track",
          "milestone": "identity-playbook-v1.0",
          "contents": "Identity-adjacent playbook content (TBAC, reference apps)"
        },
        {
          "wave": "Later conceptual track",
          "milestone": "runtime-governance-rfc-v0",
          "contents": "Runtime enforcement / data plane RFCs"
        },
        {
          "wave": "Review backlog",
          "milestone": "review-backlog",
          "contents": "Parked pending clarification or external materials"
        }
      ]
    }
  }
}
```

- [ ] **Step 2: Validate the JSON**

```bash
/Users/sarahnovotny/Github/python3.12-venv/bin/python3 -c "import json; data = json.load(open('/Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent/cosai-issue-triage/triage_milestones.json')); print('namespaces:', list(data['namespaces'].keys()), 'ws4 milestones:', len(data['namespaces']['ws4']['milestones']))"
```

Expected: `namespaces: ['ws4'] ws4 milestones: 9`.

- [ ] **Step 3: Hold commit until Task 18 (whole skill commits as a unit)**

---

## Task 18: Migrate `cosai-issue-triage` — SKILL.md

**Files:**
- Create: `scripts/agent/cosai-issue-triage/SKILL.md`

- [ ] **Step 1: Read the source**

```bash
/usr/bin/cat /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/.claude/skills.bak/triage/SKILL.md
```

- [ ] **Step 2: Write `scripts/agent/cosai-issue-triage/SKILL.md`**

```markdown
---
name: cosai-issue-triage
description: Produce a structured triage note for a GitHub issue or PR in a CoSAI workstream, matching the format established by @parmarmanojkumar.
---

# CoSAI Issue Triage Note Generator

Produce a structured triage note for a GitHub issue or PR in `{config.repo.owner}/{config.repo.name}`, matching the format established by @parmarmanojkumar.

## Arguments

Two arguments:

1. `workstream` — slug naming a file in `<repo_root>/scripts/agent/configs/<slug>.yaml`. Determines the repo, the milestone namespace inside `triage_milestones.json`, and the recognised triage labels.
2. `issue_number` — integer. The issue or PR number to triage.

If either is omitted, ask.

## Process

1. **Fetch the issue/PR** via `gh issue view <issue_number> --repo {config.repo.owner}/{config.repo.name}` or `gh pr view <issue_number> --repo ...` — read title, body, labels, existing comments (especially prior triage notes from @parmarmanojkumar to stay consistent).
2. **Cross-reference** related issues mentioned in the body or comments; skim them just enough to populate `Related/dependencies`.
3. **Classify** against the taxonomy below. Use the milestone list for `{config.triage.milestone_namespace}` in `<repo_root>/scripts/agent/cosai-issue-triage/triage_milestones.json` to pick `Proposed milestone/versioning`.
4. **Draft the triage note** using the exact template below.
5. **Present the note to the user** for review. Never post without explicit approval.

## Output template (use verbatim)

```
Triage note (YYYY-MM-DD)

Summary:
<one-line characterization of what the issue is>

Type:
<editorial | conceptual>

Recommendation:
<Accept | Accept - separate track | Accept - umbrella | Merge into related issue | Defer pending accessible materials | Reject>

Proposed wave:
<one of the waves from triage_milestones.json for this workstream>

Proposed milestone/versioning:
<one of the established milestone names from triage_milestones.json, or propose a new one with rationale>

Related/dependencies: #<n>, #<n>, ...

Reasoning:
<2-4 sentences. Why this classification, why this wave, what blocks or unblocks.>
```

## Reference taxonomy

**Types**
- `editorial` — doc structure, readability, glossary, abstract, CVE refs, diagrams
- `conceptual` — substantive content or framework change

**Recommendations**
- `Accept` — goes into the matching wave
- `Accept - separate track` — valid but too big / off-axis for the parent deliverable; gets its own milestone
- `Accept - umbrella` — coordinating/EPIC issue; execution happens in children
- `Merge into related issue` — duplicate or subset; note the target issue number
- `Defer pending accessible materials` — blocked on external content
- `Reject` — out of scope (rare; explain)

**Waves & milestones:** see `<repo_root>/scripts/agent/cosai-issue-triage/triage_milestones.json` under `namespaces.{config.triage.milestone_namespace}.milestones` for the authoritative list. If a new milestone is genuinely needed, propose it explicitly in `Proposed milestone/versioning` with a one-line rationale, and consider whether it should be added to `triage_milestones.json`.

## Follow-up triage notes

When a previously-triaged issue has evolved (new comments, scope changes, clarifications), produce a **follow-up** note rather than restating the original. Format:

```
Follow-up triage note (YYYY-MM-DD)

Status: <unchanged | upgraded on maturity | downgraded | reclassified>

<2-4 bullets on what changed since last triage>

Triage status: <restated recommendation>

<remaining gaps, if any, as a numbered list>

Related/dependencies: #<n>, ...
```

## Phase 3 issue-update flow (deferred to v2; declared in manifest)

When invoked by `cosai-meeting-agenda` (or run with an `--update-issue` flag — not in v1), this skill will:

1. Run a `gh api /repos/{config.repo.owner}/{config.repo.name}/collaborators/<user>/permission` check to determine the user's permission level.
2. If chair-level (admin/maintain/write): batched approval to post comment + apply labels (from recommendation→label mapping) + set milestone.
3. If non-chair: post comment-only with proposed labels listed in the comment text plus `cc: @<chair-handles>` for action.

v1 of this skill stops at producing the triage note; the user posts manually.

## Guardrails

- **Never post a comment without explicit user approval.** Always present the draft first.
- Match Parmar's tone: terse, structural, no emoji, no hedging language.
- Keep `Summary` to one line. `Reasoning` should be 2-4 sentences max.
- If the issue is an RFC (has `RFC` / `review` label), check whether the 3-day review window has elapsed before recommending acceptance.
- If the issue has no discernible technical content, say so in `Reasoning` and recommend `Defer pending accessible materials` or `Reject`.

## Key context

- Repo: `{config.repo.owner}/{config.repo.name}`
- Canonical triager to match: @parmarmanojkumar (across CoSAI; observe local workstream's triagers as well — see `{config.leads}` for chairs)
- Milestone namespace: `{config.triage.milestone_namespace}` — used to pick the right slice of `triage_milestones.json`.
- Today's date must come from the environment, not be guessed.
```

- [ ] **Step 3: Validate via `--validate-all`**

```bash
/Users/sarahnovotny/Github/python3.12-venv/bin/python3 /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent/render.py --validate-all
```

Expected: prints `OK   cosai-issue-triage/manifest.yaml` and `OK   cosai-meeting-agenda/manifest.yaml` and `OK   configs/ws4.yaml`. Exit 0.

- [ ] **Step 4: Dry-run render**

```bash
/Users/sarahnovotny/Github/python3.12-venv/bin/python3 /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent/render.py cosai-issue-triage --target=claude-code --dry-run
```

Expected: `DRY RUN: would render cosai-issue-triage -> ...`, exit 0.

- [ ] **Step 5: Commit the triage migration as a unit**

```bash
git add scripts/agent/cosai-issue-triage/
git commit -m "$(cat <<'EOF'
feat(scripts/agent): migrate triage skill to cosai-issue-triage/

Splits the existing .claude/skills.bak/triage/SKILL.md into manifest.yaml
+ SKILL.md, plus reshapes triage_metadata.json into triage_milestones.json
with namespace-keyed milestone lists. v1 ships only the ws4 namespace.

Phase 3 issue-update flow (chair-permission-gated label + milestone
application; comment-only with cc-to-chairs for non-chair runs) is
documented in the manifest's side_effects.v1_status: deferred and in a
new "Phase 3 issue-update flow (deferred)" section in SKILL.md.

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 19: Sync `scripts/fetch_meeting_minutes.py` from working copy

**Files:**
- Modify: `scripts/fetch_meeting_minutes.py`

The repo's copy is older (Apr 20, missing the WS3 + Code-SIG + RM-SIG sources and the HttpError-resilient export path). The working copy at `~/Github/scripts/fetch_meeting_minutes.py` has today's improvements.

- [ ] **Step 1: Compare to confirm divergence**

```bash
/usr/bin/diff /Users/sarahnovotny/Github/scripts/fetch_meeting_minutes.py /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/fetch_meeting_minutes.py | /usr/bin/head -50
```

Expected: substantive diff covering WS3/Code-SIG/RM-SIG SOURCES entries, HttpError import, try/except in fetch_drive_source, totals_errors plumbing.

- [ ] **Step 2: Copy the working version into the repo**

```bash
/bin/cp /Users/sarahnovotny/Github/scripts/fetch_meeting_minutes.py /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/fetch_meeting_minutes.py
```

- [ ] **Step 3: Verify the in-repo copy now matches**

```bash
/usr/bin/diff /Users/sarahnovotny/Github/scripts/fetch_meeting_minutes.py /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/fetch_meeting_minutes.py
```

Expected: no diff.

- [ ] **Step 4: Smoke-test the synced version (dry — argparse only)**

```bash
/Users/sarahnovotny/Github/python3.12-venv/bin/python3 /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/fetch_meeting_minutes.py --help
```

Expected: usage with `--skip-existing` flag listed.

- [ ] **Step 5: Commit**

```bash
git add scripts/fetch_meeting_minutes.py
git commit -m "$(cat <<'EOF'
chore(scripts): sync fetch_meeting_minutes.py to current working version

Brings the in-repo copy up to date with ~/Github/scripts/fetch_meeting_minutes.py.
Adds WS3, Code-SIG, RM-SIG drive sources; adds HttpError-resilient
export path so a single failed shortcut-target export does not abort
the run; adds total_errors counter to the run summary.

The cosai-meeting-agenda skill's manifest declares this script as the
out-of-band populator of meeting_minutes/<ws>/ — keeping that reference
honest requires the in-repo copy to match what users actually run.

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 20: Establish `agenda_drafts/` directory

**Files:**
- Create: `agenda_drafts/README.md`
- Create: `agenda_drafts/ws4/.gitkeep`

- [ ] **Step 1: Write `agenda_drafts/README.md`**

```markdown
# Agenda Drafts

Per-workstream agenda drafts generated by the `cosai-meeting-agenda` skill (see `scripts/agent/cosai-meeting-agenda/`) before promotion to a GitHub Discussion.

## Layout

```
agenda_drafts/
├── README.md                # this file
└── <workstream>/
    └── YYYY-MM-DD.md        # one file per upcoming meeting
```

The date is the **meeting date**, not the generation date.

## Frontmatter contract

Every draft carries the frontmatter documented in `scripts/agent/DESIGN.md` §7. Fields:

- `schema_version: 1` (constant)
- `workstream` — slug, matches a config in `scripts/agent/configs/`
- `meeting_date` — the date of the meeting this agenda is for
- `generated_at`, `generated_by`, `generated_by_role` — populated by the skill at run time
- `source_skill`, `source_skill_version` — provenance of the draft
- `status` — `draft` | `reviewed` | `promoted`
- `promoted_to`, `promoted_at` — set after promotion to a Discussion
- `supersedes` — reserved for regeneration scenarios

## Lifecycle

1. The skill writes a `status: draft` file.
2. User reviews; optionally sets `status: reviewed`.
3. On user-approved promotion: skill creates the Discussion via `gh api graphql`, then updates the file's frontmatter to `status: promoted` with `promoted_to:` + `promoted_at:` populated.
4. Files stay after promotion as an audit trail. Do not delete.

## Why drafts are tracked in the repo

Drafts in this directory are committed so:
- Any chair can review pre-meeting state without running the skill themselves.
- Diffs between consecutive drafts (or between a draft and the eventually-posted Discussion) are inspectable via `git diff`.
- Promotion is auditable: the file shows what was generated, when, and where it ended up.

Please **do not** add `agenda_drafts/` to `.gitignore`.
```

- [ ] **Step 2: Write `agenda_drafts/ws4/.gitkeep` (empty)**

```bash
/usr/bin/touch /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/agenda_drafts/ws4/.gitkeep
```

- [ ] **Step 3: Commit**

```bash
git add agenda_drafts/README.md agenda_drafts/ws4/.gitkeep
git commit -m "$(cat <<'EOF'
feat(agenda_drafts): canonical pre-promotion draft location

Adds agenda_drafts/<workstream>/ as the tracked location for agenda
drafts produced by cosai-meeting-agenda before promotion to a GitHub
Discussion. README explains the layout, frontmatter contract, and
lifecycle (draft → reviewed → promoted).

Per DESIGN.md §7: drafts use schema_version: 1, carry status + promotion
fields, and stay in the directory after promotion as audit trail.

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 21: Write `scripts/agent/README.md`

**Files:**
- Create: `scripts/agent/README.md`

- [ ] **Step 1: Write `scripts/agent/README.md`**

```markdown
# scripts/agent/

Generalised CoSAI agent-skill scaffolding. Skills here are workstream-agnostic and harness-agnostic — drop in a workstream config, render for your harness, and use.

## What's in this directory

| Path | Purpose |
|---|---|
| `DESIGN.md` | v1 design document (canonical) |
| `PLAN.md` | v1 implementation plan |
| `MANIFEST_SCHEMA.md` | Human-readable manifest field reference |
| `manifest.schema.json` | JSON Schema for skill manifests |
| `render.py` | CLI: render a skill for a target harness |
| `requirements.txt` / `requirements-dev.txt` | Python deps |
| `pytest.ini` | Test config |
| `tests/` | Unit tests for `render.py` and schema validation |
| `configs/_config.schema.json` | JSON Schema for workstream configs |
| `configs/<id>.yaml` | One file per workstream/SIG (v1 ships only `ws4.yaml`) |
| `cosai-meeting-agenda/` | Generates a meeting agenda draft for a workstream |
| `cosai-issue-triage/` | Produces a structured triage note for an issue or PR |
| `parity-reports/` | Behaviour-equivalence reports per migration |

## Quickstart (Claude Code)

```bash
# 1. Activate the shared venv (or any venv with pyyaml + jsonschema).
source ~/Github/python3.12-venv/bin/activate

# 2. Validate everything passes the schemas.
python scripts/agent/render.py --validate-all

# 3. Install the meeting-agenda skill into ~/.claude/skills/ (symlink default — repo edits live).
python scripts/agent/render.py cosai-meeting-agenda --target=claude-code

# 4. Install the triage skill the same way.
python scripts/agent/render.py cosai-issue-triage --target=claude-code

# 5. Use them in Claude Code by invoking the skill names.
```

## Adding a new workstream

A workstream is just a config file. To add one (e.g. WS3):

```bash
cp scripts/agent/configs/ws4.yaml scripts/agent/configs/ws3.yaml
# Edit ws3.yaml: change workstream.id, name, full_name, leads, meeting cadence,
# milestone namespace, etc. If the workstream is a SIG of an existing one,
# add `extends: <parent-id>` and override only the fields that differ.
python scripts/agent/render.py --validate-all   # confirms schema compliance
```

Then invoke the skill with the new slug: `cosai-meeting-agenda ws3`.

## Re-rendering after edits

If you `--symlink`-installed and edited a SKILL.md, the change is live (no re-render needed). If you edited `manifest.yaml` (which generates the auto-injected Skill Contract block), re-run:

```bash
python scripts/agent/render.py <skill-name> --target=claude-code
```

## Other harnesses

v1 supports `--target=claude-code`. `--target=generic` is reserved (emits a deferred-to-v2 notice). Codex and Gemini renderers can be added as PRs by people who use those harnesses; the manifest schema is intentionally harness-agnostic so the contract you read here holds for any consumer.

## Pre-flight: data dependencies

Some skills depend on data populated by out-of-band processes. For `cosai-meeting-agenda`: `meeting_minutes/<workstream>/` is populated by `scripts/fetch_meeting_minutes.py`. Run that first (with appropriate Drive auth — see `~/.config/mcp-gdrive/`) before generating an agenda. The renderer prints reminders for these dependencies on install.

## Further reading

- Manifest schema: `MANIFEST_SCHEMA.md`
- Design rationale: `DESIGN.md`
- Implementation plan: `PLAN.md`
- Per-skill behaviour: each skill's `SKILL.md` documents process
```

- [ ] **Step 2: Commit**

```bash
git add scripts/agent/README.md
git commit -m "$(cat <<'EOF'
docs(scripts/agent): add README.md as entry point

Walks a fresh user through validate, install, add-a-workstream,
re-render. Names the v1-supported renderer target (claude-code) and
notes that generic / Codex / Gemini are deferred. Points at DESIGN.md
and MANIFEST_SCHEMA.md for deeper reading.

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 22: Write `scripts/agent/MANIFEST_SCHEMA.md`

**Files:**
- Create: `scripts/agent/MANIFEST_SCHEMA.md`

- [ ] **Step 1: Write `scripts/agent/MANIFEST_SCHEMA.md`**

This is the human-readable companion to `manifest.schema.json`. Each top-level field gets a section: type, required/optional, semantics, example.

```markdown
# CoSAI Agent Skill Manifest — Field Reference

This document is the human-readable companion to `manifest.schema.json`. The schema is canonical; this doc explains the *why* behind each field so manifest authors can write good ones and harness implementers can interpret them correctly.

## Top-level fields

### `schema_version` (integer, required)

Version of the manifest schema itself, **not** the skill. v1 = `1`. Consumers must check this before parsing further; future schema versions may rename or restructure fields.

```yaml
schema_version: 1
```

### `name` (string, required)

The skill's identifier. Lowercase letters, digits, hyphens; starts with a letter. Must match the skill's directory name. Becomes the Claude Code frontmatter `name:`.

```yaml
name: cosai-meeting-agenda
```

### `description` (string, required)

Single-paragraph description. Becomes Claude Code's frontmatter `description:` (whitespace collapsed to one line by the renderer). Should answer: what does this skill do, and what triggers using it?

```yaml
description: |
  Generate a structured meeting agenda for a CoSAI workstream or SIG.
```

### `version` (semver string, required)

Skill version (X.Y.Z[-suffix]). Bumped per skill, independent of `schema_version`. Suffixes like `-draft`, `-rc1` allowed.

```yaml
version: 1.0.0
```

### `governance` (object, required)

CoSAI/OASIS metadata. Required keys: `license`, `ai_attribution`. Provides the AI attribution string every CoSAI commit should carry.

```yaml
governance:
  license: CC-BY-4.0
  ai_attribution: |
    Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
```

### `arguments` (array, required)

Inputs the skill takes when invoked. Each item: `name`, `type` (string|integer|boolean|array), `required` (bool), optional `description`.

```yaml
arguments:
  - name: workstream
    type: string
    required: true
    description: Workstream/SIG slug.
```

### `dependencies` (object, required)

What the skill needs to run. Three sub-keys:

#### `dependencies.tools` (array, required)

Each tool: `id` (abstract — `gh`, `filesystem`, `mcp-something`), optional `purpose`, `required` (bool), `capabilities` (array of `read`/`write`/`exec`). Harnesses map abstract IDs to their concrete implementations.

```yaml
dependencies:
  tools:
    - id: gh
      purpose: Read issues, PRs, discussions
      required: true
      capabilities: [read]
```

#### `dependencies.configs` (array, optional)

Workstream / per-skill config files the skill consumes. Each: `path` (relative to the skill or repo root), optional `schema` (path to JSON Schema for validation).

```yaml
dependencies:
  configs:
    - path: configs/{workstream}.yaml
      schema: configs/_config.schema.json
```

#### `dependencies.data` (array, optional)

Data paths the skill reads or writes at run time. Each: `path`, `access` (`read`/`write`/`read-write`), `runtime_role` (`input`/`output`), `provisioning` (object).

The `provisioning` block describes how the data path comes to exist. `kind` is one of:
- `in-repo` — committed in the repo, available immediately after clone
- `out-of-band` — populated by a separate process (sync script, manual setup); the skill cannot create it
- `runtime-fetched` — the skill fetches at run time (e.g. from a remote API)

For `out-of-band`, include `populated_by` (with `tool`, `repo`, `documented_at`), `cadence`, and `on_missing` (recovery instructions).

```yaml
dependencies:
  data:
    - path: "{config.meeting.meeting_minutes_dir}/"
      access: read
      runtime_role: input
      provisioning:
        kind: out-of-band
        tracked_in_repo: false
        populated_by:
          tool: scripts/fetch_meeting_minutes.py
          repo: cosai-oasis/ws4-secure-design-agentic-systems
        on_missing: |
          Halt and instruct the user to run scripts/fetch_meeting_minutes.py.
```

### `composition` (object, optional)

Inter-skill calls. Two arrays:

- `calls` — skills this one invokes. Each: `skill`, `mode` (`required`/`optional`), `condition`, `passes`, `receives`.
- `called_by` — skills that invoke this one (informational; lets a manifest reader trace incoming dependencies).

```yaml
composition:
  calls:
    - skill: cosai-issue-triage
      mode: optional
      condition: An issue lacks recognised triage labels.
      passes: { issue_number: "<issue.number>" }
      receives: { triage_note: markdown }
```

### `output` (object, required)

What the skill produces.

#### `output.primary` (object, required)

The deterministic primary artefact. Always produced. Fields: `type` (`markdown`/`yaml`/`json`/...), `location` (path template), optional `frontmatter` (object describing frontmatter fields).

```yaml
output:
  primary:
    type: markdown
    location: agenda_drafts/{workstream}/{meeting_date}.md
```

#### `output.side_effects` (array, optional)

Side effects gated on user approval (or a runtime condition). Each: `kind`, `condition`, `action`, optional `v1_status` (`implemented`/`deferred`).

```yaml
side_effects:
  - kind: github-discussion
    condition: user explicitly approves promotion
    action: Create discussion in {config.repo} matching the agenda template.
```

### `boundaries` (object, required)

`does_not` (array, ≥1 item) — explicit non-actions. The skill MUST refuse these even if asked.

```yaml
boundaries:
  does_not:
    - Post to a GitHub Discussion without explicit user approval
```

### `failure_modes` (array, required, ≥1 item)

Each entry: `condition` + `action`. Lets harnesses wire halt/recover behaviour without re-reading the prose.

```yaml
failure_modes:
  - condition: meeting_minutes/<workstream>/ missing or empty
    action: Halt with the expected directory path.
```

### `narrative` (string, required, default `SKILL.md`)

Filename of the prose body. Almost always `SKILL.md`. Resolved relative to the skill's directory.

```yaml
narrative: SKILL.md
```

## Templating

Path values may contain template placeholders:

- `{workstream}` — the runtime argument (preserved in rendered SKILL.md, resolved by the model)
- `{config.X.Y}` — a field from the loaded workstream config (resolved at run time by the model)
- `{meeting_date}` — runtime-derived
- `<repo_root>` — substituted at render time by `render.py` with the absolute repo path

## What NOT to put in the manifest

- The imperative process narrative — that's `SKILL.md`'s job
- Hardcoded workstream values — those go in `configs/<id>.yaml`
- Claude Code-specific frontmatter — the renderer generates it
- License or governance text beyond the brief reference — those live in repo-level docs

## See also

- `manifest.schema.json` — machine-readable contract
- `DESIGN.md` §5 — original design rationale for field choices
- `cosai-meeting-agenda/manifest.yaml` — the most complete worked example
```

- [ ] **Step 2: Commit**

```bash
git add scripts/agent/MANIFEST_SCHEMA.md
git commit -m "$(cat <<'EOF'
docs(scripts/agent): add MANIFEST_SCHEMA.md — human-readable manifest reference

Companion to manifest.schema.json. Each top-level field documented with
type, required/optional, semantics, and an example. Covers templating
conventions ({workstream}, {config.X.Y}, <repo_root>) and explicitly
calls out what does NOT belong in the manifest (process narrative,
hardcoded workstream values, harness-specific frontmatter).

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 23: Generate parity report — `cosai-meeting-agenda`

**Files:**
- Create: `scripts/agent/parity-reports/cosai-meeting-agenda-2026-05-08.md`

The parity report verifies the new skill produces semantically equivalent output to the old one for at least one real-world input.

- [ ] **Step 1: Identify a known-good input**

Pick the most recent posted WS4 agenda Discussion. Likely the previous Thursday's agenda (Discussion #84 was the canonical-template anchor; pick the most recent agenda Discussion as input).

```bash
/opt/homebrew/bin/gh discussion list --repo cosai-oasis/ws4-secure-design-agentic-systems --limit 5 2>&1
```

(If `gh discussion list` is not in your gh version, use `gh api`):

```bash
/opt/homebrew/bin/gh api graphql -f query='{ repository(owner: "cosai-oasis", name: "ws4-secure-design-agentic-systems") { discussions(first: 5, orderBy: {field: CREATED_AT, direction: DESC}) { nodes { number title } } } }' 2>&1
```

- [ ] **Step 2: Run the OLD skill**

Skip if you don't have the old skill installed. Otherwise: invoke the existing `agenda` skill against today's WS4 state and capture its output.

If the old skill is not currently installed, document this as "old-skill output captured from the most recent posted agenda Discussion (#NN) on YYYY-MM-DD."

- [ ] **Step 3: Run the NEW skill**

After installing via `render.py cosai-meeting-agenda --target=claude-code`, invoke it via Claude Code with `workstream=ws4`. Capture the draft written to `agenda_drafts/ws4/<date>.md`.

- [ ] **Step 4: Diff**

```bash
/usr/bin/diff -u <old-output> <new-output> | /usr/bin/head -120
```

- [ ] **Step 5: Write the parity report**

```markdown
# cosai-meeting-agenda — parity report (2026-05-08)

**Goal:** Verify the migrated `cosai-meeting-agenda` skill produces semantically equivalent output to the legacy `agenda` skill for a known-good input.

## Input case

- Workstream: WS4
- Meeting date: 2026-05-08
- Reference: most recent posted agenda Discussion (#NN, 2026-MM-DD)

## Old-skill output (reference snapshot)

(Pasted verbatim from the posted Discussion, or from a captured run of the legacy skill — whichever is available. Source:  the legacy skill's last invocation OR the posted Discussion.)

```markdown
<old output here>
```

## New-skill output

(Pasted verbatim from `agenda_drafts/ws4/2026-05-08.md`, with frontmatter included.)

```markdown
<new output here>
```

## Semantic equivalence assessment

| Section | Old | New | Match? | Notes |
|---|---|---|---|---|
| Action Item Follow-ups | <count> items | <count> items | ✓ / ✗ | Same owners, same items? |
| PRs Needing Review | <count> PRs | <count> PRs | ✓ / ✗ | |
| Issues Needing Chair Decision | <count> | <count> | ✓ / ✗ | |
| New Issues Since Last Meeting | <count> | <count> | ✓ / ✗ | |
| Cross-Stream Updates | <count> | <count> | ✓ / ✗ | |

## Deltas

(Itemise any differences, with one-line explanations.)

- **Frontmatter present (new only).** The new skill writes a tracked draft file with frontmatter; the old skill produced inline output only. Expected.
- **WS4 lead names externalised.** "Sarah Novotny, Ian Molloy" no longer appears in the body — those values come from `configs/ws4.yaml`'s `leads:` and are referenced via `{config.leads}`. Expected.
- (Add more as observed.)

## Verdict

- [x] / [ ] Semantically equivalent. Migration parity confirmed.
- [ ] Discrepancies found requiring follow-up. Detailed below.

## Reproduction steps

```bash
# Install new skill
python scripts/agent/render.py cosai-meeting-agenda --target=claude-code

# In Claude Code:
# > Use cosai-meeting-agenda with workstream ws4

# Resulting draft at:
# agenda_drafts/ws4/2026-05-08.md
```
```

- [ ] **Step 6: Commit**

```bash
git add scripts/agent/parity-reports/cosai-meeting-agenda-2026-05-08.md
git commit -m "$(cat <<'EOF'
docs(scripts/agent): parity report for cosai-meeting-agenda migration

Verifies the migrated skill produces semantically equivalent output to
the legacy agenda skill for the 2026-05-08 WS4 meeting input. Documents
expected deltas (frontmatter present in new only; WS4 lead names
externalised to configs/ws4.yaml).

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 24: Generate parity report — `cosai-issue-triage`

**Files:**
- Create: `scripts/agent/parity-reports/cosai-issue-triage-2026-05-08.md`

Same approach as Task 23 but for the triage skill. Pick a recently triaged issue (look for @parmarmanojkumar's most recent triage comment) and verify the new skill produces a semantically equivalent note.

- [ ] **Step 1: Find a recently triaged issue**

```bash
/opt/homebrew/bin/gh issue list --repo cosai-oasis/ws4-secure-design-agentic-systems --search 'commenter:parmarmanojkumar' --limit 5 --json number,title,updatedAt 2>&1 | /Users/sarahnovotny/Github/python3.12-venv/bin/python3 -m json.tool
```

Pick the most recent.

- [ ] **Step 2: Capture old-skill triage**

Find @parmarmanojkumar's actual triage comment on that issue. That IS the canonical-format reference.

```bash
/opt/homebrew/bin/gh issue view <NN> --repo cosai-oasis/ws4-secure-design-agentic-systems --comments 2>&1 | /usr/bin/grep -B2 -A20 "Triage note"
```

- [ ] **Step 3: Run the NEW skill**

Via Claude Code: `cosai-issue-triage workstream=ws4 issue_number=<NN>`. Capture the produced triage note (it stays in chat — copy verbatim).

- [ ] **Step 4: Write the parity report**

```markdown
# cosai-issue-triage — parity report (2026-05-08)

**Goal:** Verify the migrated `cosai-issue-triage` skill produces semantically equivalent output to @parmarmanojkumar's manual triage format.

## Input case

- Workstream: WS4
- Issue: #<NN>
- @parmarmanojkumar's reference triage: dated YYYY-MM-DD

## Reference triage (from @parmarmanojkumar's comment)

```
<paste verbatim>
```

## New-skill triage output

```
<paste verbatim>
```

## Semantic equivalence assessment

| Field | Reference | New | Match? |
|---|---|---|---|
| Summary | <one line> | <one line> | ✓ / ✗ |
| Type | editorial / conceptual | editorial / conceptual | ✓ / ✗ |
| Recommendation | <verb> | <verb> | ✓ / ✗ |
| Proposed wave | <wave> | <wave> | ✓ / ✗ |
| Proposed milestone/versioning | <milestone> | <milestone> | ✓ / ✗ |
| Related/dependencies | #..., #... | #..., #... | ✓ / ✗ |
| Reasoning length | N sentences | M sentences | ✓ if 2-4 |

## Deltas

(Same shape as Task 23.)

## Verdict

- [x] / [ ] Semantically equivalent. Migration parity confirmed.
```

- [ ] **Step 5: Commit**

```bash
git add scripts/agent/parity-reports/cosai-issue-triage-2026-05-08.md
git commit -m "$(cat <<'EOF'
docs(scripts/agent): parity report for cosai-issue-triage migration

Verifies the migrated skill produces semantically equivalent output to
@parmarmanojkumar's manual triage format on a real recently-triaged
WS4 issue. Documents expected deltas (file-rooted milestones reference
via triage_milestones.json namespaces.ws4 instead of inline).

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 25: Update `CONTRIBUTING.md`

**Files:**
- Modify: `CONTRIBUTING.md`

The reorg branch's `CONTRIBUTING.md` does not yet have a tooling section. Add a one-paragraph pointer.

- [ ] **Step 1: Read current CONTRIBUTING.md**

```bash
/usr/bin/cat /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/CONTRIBUTING.md
```

- [ ] **Step 2: Add a "Working with WS4 tooling" section before "## Questions?"**

Use the Edit tool to insert a new section. The new section:

```markdown
## Working with WS4 tooling

Repeatable PM tasks (meeting agendas, issue triage) are scaffolded in `scripts/agent/`. Skills there are workstream-agnostic (drop a config in `scripts/agent/configs/`) and harness-aware (Claude Code today; the manifest schema is intentionally portable for other agentic harnesses). See `scripts/agent/README.md` for install + use.

```

- [ ] **Step 3: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "$(cat <<'EOF'
docs(contributing): add Working with WS4 tooling pointer

One-paragraph addition pointing contributors at scripts/agent/README.md
for the meeting-agenda + issue-triage tooling. Lands above Questions?

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 26: Update `CLAUDE.md` (working tree only — do not stage if untracked)

**Files:**
- Modify: `CLAUDE.md` (working tree)

Per DESIGN.md §9, this update describes only the new pathway and notes legacy `.bak` skills are deprecated locally.

- [ ] **Step 1: Check if CLAUDE.md is tracked**

```bash
git -C /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems ls-files CLAUDE.md
```

- If empty: file is **untracked**. Update the working tree but do NOT `git add`. Note in the v1 PR description.
- If `CLAUDE.md` is printed: file IS tracked. Update and commit.

- [ ] **Step 2: Read current CLAUDE.md**

```bash
/usr/bin/cat /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/CLAUDE.md
```

- [ ] **Step 3: Update the "Agent Behavior Guidelines" / project-scoped skills section**

Find the existing reference to `.claude/skills/` (legacy `agenda` and `triage`) and replace it with a description of the new pathway. Use Edit to make a surgical change. The new content describes:

- Skills now live in `scripts/agent/` and are installed via `python scripts/agent/render.py <skill> --target=claude-code`.
- The legacy `.claude/skills.bak/` location is deprecated locally; do not edit there.
- New skills: `cosai-meeting-agenda` (was `agenda`) and `cosai-issue-triage` (was `triage`). Both take a `workstream` argument.
- See `scripts/agent/README.md` for install and use.

- [ ] **Step 4: If untracked: stop here, do not stage**

Per DESIGN.md §9 + Step 1's check: if the file is untracked, the working-tree update is the deliverable; do not commit.

- [ ] **Step 5: If tracked: commit**

```bash
git add CLAUDE.md
git commit -m "$(cat <<'EOF'
docs(claude.md): point at new scripts/agent/ skill pathway

Replaces references to the legacy .claude/skills/ pathway with the new
scripts/agent/ + render.py installer flow. Notes the renamed skills
(cosai-meeting-agenda, cosai-issue-triage) and the `workstream` argument
that drives multi-workstream support.

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 27: Add CI gate for `--validate-all`

**Files:**
- Create: `.github/workflows/agent-validate.yml`

- [ ] **Step 1: Check if the repo already has GitHub Actions workflows**

```bash
/bin/ls -la /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/.github/workflows/ 2>&1
```

If the directory doesn't exist or is empty, this is the first workflow.

- [ ] **Step 2: Write `.github/workflows/agent-validate.yml`**

```yaml
name: Validate scripts/agent manifests and configs

on:
  pull_request:
    paths:
      - 'scripts/agent/**'
  push:
    branches: [main, reorg]
    paths:
      - 'scripts/agent/**'

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install runtime deps
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r scripts/agent/requirements-dev.txt

      - name: Run --validate-all
        run: python scripts/agent/render.py --validate-all

      - name: Run pytest
        run: python -m pytest scripts/agent/tests/ -v
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/agent-validate.yml
git commit -m "$(cat <<'EOF'
ci: validate scripts/agent manifests and configs on PR

GitHub Actions workflow runs render.py --validate-all and pytest on
any change under scripts/agent/. Triggers on pull_request and on push
to main/reorg. Uses Python 3.12 and the dev requirements pinned in
scripts/agent/requirements-dev.txt.

Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
EOF
)"
```

---

## Task 28: Final verification — full pipeline from scratch

**Files:** none

This is the v1 acceptance check. Run all 14 acceptance criteria from DESIGN.md §11.

- [ ] **Step 1: Schema validation passes**

```bash
/Users/sarahnovotny/Github/python3.12-venv/bin/python3 /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent/render.py --validate-all
```

Expected: every manifest and config validated, exit 0.

- [ ] **Step 2: All tests pass**

```bash
cd /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent && /Users/sarahnovotny/Github/python3.12-venv/bin/pytest -v
```

Expected: 13 passed (or whatever final count is — all pass).

- [ ] **Step 3: Dry-run renders succeed**

```bash
/Users/sarahnovotny/Github/python3.12-venv/bin/python3 /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent/render.py cosai-meeting-agenda --target=claude-code --dry-run
/Users/sarahnovotny/Github/python3.12-venv/bin/python3 /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent/render.py cosai-issue-triage --target=claude-code --dry-run
```

Both: exit 0 with intent printed.

- [ ] **Step 4: Real install works**

```bash
/Users/sarahnovotny/Github/python3.12-venv/bin/python3 /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent/render.py cosai-meeting-agenda --target=claude-code
/Users/sarahnovotny/Github/python3.12-venv/bin/python3 /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent/render.py cosai-issue-triage --target=claude-code
/bin/ls -la ~/.claude/skills/cosai-meeting-agenda/ ~/.claude/skills/cosai-issue-triage/
```

Expected: SKILL.md present in both (symlinks back to repo's staging files); `triage_milestones.json` symlinked into `cosai-issue-triage/`.

- [ ] **Step 5: Generic-target stub returns proper exit code**

```bash
/Users/sarahnovotny/Github/python3.12-venv/bin/python3 /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/agent/render.py cosai-meeting-agenda --target=generic; echo "exit=$?"
```

Expected: stderr says "Generic-prompt rendering deferred to v2"; exit code 2.

- [ ] **Step 6: agenda_drafts/ structure correct**

```bash
/bin/ls -la /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/agenda_drafts/
/bin/cat /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/agenda_drafts/README.md | /usr/bin/head -3
```

Expected: README.md and ws4/.gitkeep present.

- [ ] **Step 7: fetch_meeting_minutes.py is current**

```bash
/usr/bin/diff /Users/sarahnovotny/Github/scripts/fetch_meeting_minutes.py /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems/scripts/fetch_meeting_minutes.py
```

Expected: no diff (synced).

- [ ] **Step 8: All 14 acceptance criteria mapped to deliverables**

Walk through DESIGN.md §11 and check off each criterion against the work done. Document any unmet criteria in the v1 PR description.

- [ ] **Step 9: Open the v1 PR**

```bash
git -C /Users/sarahnovotny/Github/ws4-secure-design-agentic-systems push -u origin tooling/agent-skills

/opt/homebrew/bin/gh pr create --repo cosai-oasis/ws4-secure-design-agentic-systems --base reorg --head tooling/agent-skills --title "tooling: scripts/agent/ — generalised CoSAI agent skills (v1)" --body "$(cat <<'EOF'
## Summary

Lands v1 of `scripts/agent/`: a generalisable scaffolding for CoSAI's
recurring AI-assisted PM tasks (meeting agenda generation, issue triage).

- **Manifest schema** (`manifest.schema.json` + `MANIFEST_SCHEMA.md`): structured contract every skill conforms to. Harness-agnostic.
- **Workstream config schema** (`configs/_config.schema.json`): single-level `extends:` inheritance for SIGs.
- **Two migrated skills**: `cosai-meeting-agenda` (was `agenda`) and `cosai-issue-triage` (was `triage`). WS4 specifics moved to `configs/ws4.yaml`; SKILL.md uses `{config.X}` references resolved at run time.
- **Renderer** (`render.py`): `--target=claude-code` (symlink default), `--target=generic` (v2 stub), `--validate-all` (CI gate).
- **Canonical agenda draft location**: `agenda_drafts/<workstream>/YYYY-MM-DD.md` with frontmatter contract.
- **Bundled `fetch_meeting_minutes.py` sync**: in-repo copy now matches the production version (WS3 + Code-SIG + RM-SIG sources, HttpError-resilient export).
- **Parity reports**: semantic-equivalence checks for both migrated skills.
- **CI gate**: GitHub Actions workflow runs `--validate-all` and pytest on every PR touching `scripts/agent/`.

## Alignment with upstream CoSAI documents

- **OASIS CoSAI AI Usage Guidelines**: governance block in every manifest.
- **secure-ai-tooling#149** (vendor-neutral attribution): every commit on this branch uses `Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>`.
- **WS4 CONTRIBUTING.md AI Usage Policy**: this PR was drafted with substantial AI assistance — see disclosure below.

## What's deferred to v2

- Workstream configs for WS3, ADLC, RM-SIG, Code-SIG (drop-in PRs once schema is settled).
- Generic-prompt renderer (`--target=generic` — CLI accepts the flag for forward-compat).
- Phase 3 composition: `cosai-meeting-agenda` invokes `cosai-issue-triage` inline for unlabeled issues, with chair-permission-gated update flow. Manifest declares the composition; implementation follows.
- Codex / Gemini renderers — open to PRs from people who use those harnesses.

## AI assistance disclosure

This PR was drafted with substantial AI assistance (Claude Code, Opus 4.7). The brainstorming session resolved 6 design questions; the design doc, schema, manifests, render.py, and SKILL.md migrations were authored by Claude with iterative direction from Sarah. Each commit uses the CoSAI vendor-neutral trailer; this PR description carries the substantive transparency.

## Acceptance criteria

All 14 criteria from `scripts/agent/DESIGN.md` §11 are met. See parity reports under `scripts/agent/parity-reports/` for the semantic-equivalence verifications.

## Test plan

- [x] `python scripts/agent/render.py --validate-all` exits 0
- [x] `pytest scripts/agent/tests/ -v` passes
- [x] Dry-run renders succeed for both skills
- [x] Real install creates symlinks in `~/.claude/skills/`
- [ ] Reviewer reads DESIGN.md, MANIFEST_SCHEMA.md, README.md and confirms the contract is clear
- [ ] Reviewer scans the parity reports and confirms semantic equivalence with the legacy skills
- [ ] CI passes on this PR
EOF
)"
```

- [ ] **Step 10: PR opened — share URL with the user**

After PR is created, output the URL. The PR is ready for review against `reorg`.

---

## Self-review: spec coverage check

Walked DESIGN.md §11's 14 acceptance criteria against the tasks above:

| # | Criterion | Tasks |
|---|---|---|
| 1 | scripts/agent/ exists with the directory layout | Tasks 1, 2, 7, 13, 14, 15, 16, 17, 18 |
| 2 | manifest.schema.json + configs/_config.schema.json validate worked examples | Tasks 3, 5, 6, 13 |
| 3 | MANIFEST_SCHEMA.md documents every field | Task 22 |
| 4 | cosai-meeting-agenda manifest + SKILL.md + render dry-run exits 0 | Tasks 14, 15 |
| 5 | cosai-issue-triage manifest + SKILL.md + triage_milestones.json + render dry-run exits 0 | Tasks 16, 17, 18 |
| 6 | configs/ws4.yaml exists and validates | Task 13 |
| 7 | render.py --validate-all exits 0 with all artefacts | Tasks 8, 28 |
| 8 | Parity reports for both skills | Tasks 23, 24 |
| 9 | scripts/agent/README.md walks fresh user through install | Task 21 |
| 10 | CONTRIBUTING.md has tooling pointer | Task 25 |
| 11 | CLAUDE.md updated for new pathway | Task 26 |
| 12 | agenda_drafts/ exists with placeholder/README | Task 20 |
| 13 | CI gate runs --validate-all on PR | Task 27 |
| 14 | scripts/fetch_meeting_minutes.py synced | Task 19 |

All 14 mapped. No gaps.

## Self-review: placeholder scan

Scanned for: TBD, TODO, "implement later", "fill in details", "add appropriate error handling", "Similar to Task N", references to undefined functions.

- One legitimate placeholder: parity reports (Tasks 23, 24) include `<paste verbatim>` — these are placeholders for the *parity-report-author* to fill at the moment of writing. The plan steps before that placeholder produce the content the author pastes in. Clearly indicated.
- "old-skill output captured from..." in Task 23 step 2 — covers the case where the legacy skill is no longer installed. Not a TBD; an explicit fallback.

No code-step placeholders. All test code, all schema content, all SKILL.md content, all manifest content, all CLI behaviour is fully specified.

## Self-review: type/name consistency

Spot-checked:

- `render_claude_code(skill_dir, output_dir, *, symlink, repo_root)` — same signature in Task 10, 11, 12.
- `_validate_manifest`, `_validate_config`, `_load_yaml`, `_load_json`, `_load_manifest` — all defined in Task 8, used consistently in Tasks 9-12.
- Manifest field names — `schema_version`, `name`, `description`, `version`, `governance`, `arguments`, `dependencies`, `composition`, `output`, `boundaries`, `failure_modes`, `narrative` — used identically in `manifest.schema.json`, every manifest, MANIFEST_SCHEMA.md.
- Config field names — `schema_version`, `extends`, `workstream`, `repo`, `leads`, `meeting`, `channels`, `triage` — consistent.

No inconsistencies found.

---

## Execution Handoff

**Plan complete and saved to `scripts/agent/PLAN.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration with separation of concerns.

**2. Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints for review.

Which approach?
