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
