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
