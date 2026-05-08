# CoSAI Agent Skills — v1 Design

**Status:** Draft
**Date:** 2026-05-08
**Branch:** `tooling/agent-skills`
**Author:** Sarah Novotny (with AI assistance — see *Provenance* below)

---

## 1. Context

CoSAI workstreams use AI assistants for repetitive PM tasks: producing meeting agendas, triaging issues against the workstream's milestone taxonomy, summarising activity. Today, two skills do this for WS4:

- `agenda` — generates a WS4 or ADLC SIG meeting agenda from minutes, issues, and PRs.
- `triage` — produces a structured triage note for a WS4 issue or PR, matching @parmarmanojkumar's format.

These skills currently live at `~/.claude/skills.bak/{agenda,triage}/` (project-scoped, gitignored locally, byte-identical to `sarahnovotny/cosai-claude/skills/`). They are tightly coupled to:

- The Claude Code skill format (YAML frontmatter + markdown body).
- WS4-specific values hardcoded into the prose (repo URL, lead names, meeting cadence, Discussion #84 as the canonical agenda template, MemPalace drawer IDs).
- The author's local environment (assumes `gh` CLI, `mcp-gdrive`, the WS4 repo at a known path).

CoSAI is positioned as broadly any-agent friendly. The skills, in their current form, are usable only by Claude Code users in WS4 or ADLC. WS3, the SIGs under WS3 (Code-SIG, RM-SIG), and any future workstream cannot adopt them without copy-paste-and-edit.

This design generalises the skills along two axes:

1. **Cross-CoSAI portability.** Same skill, different workstream — drop in a config file, no changes to skill prose.
2. **Cross-harness portability.** Same skill, different agentic harness — manifest carries enough structured contract for non-Claude-Code harnesses to render the skill in their native format.

A separate but related goal: canonicalise a tracked location inside the repo for *draft* agendas before they are promoted to GitHub Discussions.

---

## 2. Goals and non-goals

### Goals (v1)

- Establish a manifest schema (YAML) that carries the structured contract for every skill: dependencies, input/output, composition, boundaries, failure modes, governance.
- Establish a workstream config schema with single-level inheritance.
- Migrate `agenda` and `triage` to the new shape, preserving behaviour.
- Ship one worked workstream config (WS4) — proves the pattern.
- Ship a Claude Code renderer that installs a skill from `scripts/agent/<skill>/` into `~/.claude/skills/<skill>/`.
- Establish `agenda_drafts/<workstream>/YYYY-MM-DD.md` as the canonical pre-promotion draft location.
- Validate the schema in CI.

### Non-goals (v1; explicitly deferred)

- Codex and Gemini CLI renderers — let those be PRs from people who actually use those harnesses.
- The generic-prompt renderer — the CLI accepts the flag but emits a "v2" stub.
- Configs for any workstream other than WS4 — drop-in PRs once the schema is settled.
- Phase 3 composition (`agenda` invokes `triage` inline for unlabeled issues, then offers to update the issue with a chair-permission-aware comment + label proposal) — declared in the manifest's `composition` block so the contract is forward-compatible, but the implementation lands in a follow-on PR.
- Deprecation of `sarahnovotny/cosai-claude/skills` — left alone.

### Non-goals (v2+; out of scope of this document)

- A CoSAI-wide base config (`_cosai.yaml`) above the workstream level. May be useful once 3+ configs share the same boilerplate; until then, premature.
- Auto-publishing the skills to a registry consumable by non-WS4 contributors without cloning this repo.
- Migration of any other tooling (e.g. `fetch_meeting_minutes.py`) into the same structure.

---

## 3. Decisions summary

| # | Topic | Decision |
|---|---|---|
| 1 | Source-of-truth shape | Co-equal `manifest.yaml` (structured contracts) + `SKILL.md` (process narrative). Both hand-maintained. |
| 2 | Config inheritance | Single-level via `extends:`. Object fields deep-merge; array fields fully replace; `null` explicitly clears; schema versions must match. |
| 3 | Draft location | `agenda_drafts/<workstream>/YYYY-MM-DD.md`, tracked in repo, frontmatter with `schema_version`, `status`, promotion-link fields. Drafts kept after promotion (audit trail). |
| 4 | Issue-update flow (Phase 3, deferred) | Runtime permission check via `gh api`. Chair → full comment + labels + milestone with batched approval. Non-chair → comment-only with proposed labels and `cc: @chairs` for action. |
| 5 | Phase 4 cross-harness | Schema + JSON Schema + Claude Code renderer + generic-prompt renderer (stub in v1). Codex/Gemini renderers deferred. |
| 6 | v1 scope | Schema + migrate both skills + WS4 config only + Claude Code renderer + `agenda_drafts/`. Other configs and composition follow-on. |
| 7 | Re-run behaviour for same-day draft | Overwrite in place. Git history is the audit trail. |
| 8 | `generated_by` and `schema_version` in draft frontmatter | Both kept. |
| 9 | Renderer install default | Symlink (`--symlink`), so repo edits are live in `~/.claude/skills/`. `--copy` available for frozen installs. |
| 10 | CLAUDE.md update | Update CLAUDE.md to describe only the new pathway; note `.bak` skills are deprecated locally. |
| 11 | Out-of-band data dependencies | First-class `provisioning` sub-block on data dependencies, with `kind: out-of-band`, `tracked_in_repo: false`, `populated_by`, `on_missing`. |

---

## 4. Directory layout

```
scripts/agent/
├── DESIGN.md                          # this document
├── README.md                          # entry point: what this is, how to use, links
├── MANIFEST_SCHEMA.md                 # human-readable manifest field reference
├── manifest.schema.json               # JSON Schema for CI validation
├── render.py                          # CLI: render.py <skill> --target=<target>
├── configs/
│   ├── _config.schema.json            # JSON Schema for workstream configs
│   └── ws4.yaml                       # WS4 workstream config (v1 ships only this)
├── cosai-meeting-agenda/
│   ├── manifest.yaml
│   └── SKILL.md
├── cosai-issue-triage/
│   ├── manifest.yaml
│   ├── SKILL.md
│   └── triage_milestones.json         # workstream-keyed milestone taxonomy
└── parity-reports/                    # behaviour-equivalence reports per migration
    └── <skill>-<date>.md               # added per migration; see §10
```

(The `agenda_drafts/<workstream>/` directory lives at repo root, not under `scripts/agent/` — see §7.)

**Naming choices:**

- Skills get a `cosai-` prefix (`cosai-meeting-agenda`, `cosai-issue-triage`). They are CoSAI-conventions-aware (RFC process, OASIS governance, vendor-neutral attribution); the prefix distinguishes them from generic skills if installed user-globally.
- `MANIFEST_SCHEMA.md` is the human-readable contract description (the OASIS-standards-track style artefact); `manifest.schema.json` is the machine-readable companion used by CI.
- `render.py` lives at the top of `scripts/agent/`, not per-skill, so it can render any skill with `<skill>` as a positional arg.
- `triage_milestones.json` (renamed from the old `triage_metadata.json`) is workstream-keyed (`{ "namespaces": { "ws4": { "milestones": [...] } } }`) so future workstreams slot in without forking the file.

**Repo placement note:**

`scripts/agent/` is added to the reorg branch's tracked paths. It is *not* added to the README's directory listing in v1 — it is tooling, not deliverable content. `scripts/README.md` (or a one-line addition to `CONTRIBUTING.md`) points at `scripts/agent/README.md`.

---

## 5. Manifest schema

The manifest carries structured contracts; SKILL.md carries the imperative process narrative. Manifest is canonical for everything that needs to be machine-readable; SKILL.md is canonical for everything a human reads to understand the procedure.

### Top-level fields

| Field | Type | Required | Purpose |
|---|---|---|---|
| `schema_version` | int | yes | Version of the manifest schema itself. v1 = `1`. |
| `name` | string | yes | Skill ID. Matches the directory name. |
| `description` | string | yes | Single-paragraph description. Becomes the Claude Code frontmatter `description:`. |
| `version` | semver | yes | Skill version. Bumped per skill, independent of `schema_version`. |
| `governance` | object | yes | License, AI attribution convention, OASIS framing. |
| `arguments` | array | yes | Typed, required-flagged inputs the skill takes when invoked. |
| `dependencies` | object | yes | `tools`, `configs`, `data`. Tools have abstract IDs + capabilities. |
| `composition` | object | optional | `calls` (skills this one invokes) and `called_by` (skills that invoke this one). |
| `output` | object | yes | `primary` (always produced) and `side_effects` (only with approval). |
| `boundaries` | object | yes | `does_not:` array — explicit non-actions. |
| `failure_modes` | array | yes | Each item: `condition` + `action`. |
| `narrative` | string | yes | Filename of the prose body, almost always `SKILL.md`. |

### Worked example: `cosai-meeting-agenda/manifest.yaml`

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
          to fetching from Drive directly — the sync is its own concern with
          its own auth and credential lifecycle.
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
        labels listed in config.triage.recognised_triage_labels.
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
      generated_by_role: enum [chair, supporting, contributor]
      source_skill: string
      source_skill_version: semver
      status: enum [draft, reviewed, promoted]
      promoted_to: string?
      promoted_at: timestamp?
      supersedes: string?
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

### Field-level rationale

- **`schema_version: 1`** at the manifest level (not the skill level) lets the manifest contract evolve without bumping every skill's `version`.
- **`governance`** at the top of every manifest puts CoSAI's AI attribution convention in front of every harness that consumes the manifest, instead of relying on contributors remembering it.
- **`dependencies.tools`** uses abstract IDs (`gh`, `filesystem`) with `capabilities`. A harness without `gh` CLI but with a GitHub MCP server can map `id: gh, capabilities: [read]` to its own implementation. This is the structural lever for "any-agent friendly".
- **`dependencies.data[*].provisioning`** distinguishes how a path comes to exist:
  - `in-repo` — committed to the repo (configs, milestones, draft outputs).
  - `out-of-band` — populated by a separate process; not the skill's concern (e.g. `meeting_minutes/` populated by `fetch_meeting_minutes.py`).
  - `runtime-fetched` — the skill itself fetches at runtime (none in v1).
- **`composition.calls` and `called_by`** are first-class. Phase 3's flow is declarable now, even though implementation lands later, so the contract is forward-compatible.
- **`output.side_effects[*].v1_status: deferred`** is an explicit marker on the side effect that exists in the contract but is not implemented in this version. Lets a manifest reader know "this is real, just not yet."
- **`boundaries.does_not`** and **`failure_modes`** borrow from upstream agent contract style. Each `failure_mode` has a `condition` + `action`, so harnesses can wire halt/recover behaviour without re-reading prose.

### What the manifest does NOT carry

- The imperative step-by-step process. That stays in SKILL.md.
- Hardcoded WS4 values (lead names, repo URL, etc.). Those are in `configs/ws4.yaml`.
- The Claude Code-specific frontmatter format. That is the renderer's job.

---

## 6. Workstream config schema

Single-level inheritance via `extends:`. Configs live at `scripts/agent/configs/<id>.yaml`. v1 ships only `ws4.yaml`.

### Top-level fields

| Field | Type | Required | Purpose |
|---|---|---|---|
| `schema_version` | int | yes | Config schema version. v1 = `1`. |
| `extends` | string | optional | Parent config id. Single-level only. Omit for top-level workstreams. |
| `workstream` | object | yes | Identity: `id`, `name`, `full_name`, `parent_workstream`. |
| `repo` | object | yes (or inherited) | `owner`, `name`. |
| `leads` | array | yes (or inherited) | Each entry: `name`, `github`, `role` (chair/supporting/contributor). |
| `meeting` | object | yes (or inherited) | Cadence, time, minutes dir, filename pattern, agenda template discussion #, fallback dir. |
| `channels` | object | yes (or inherited) | Slack workspace+channel; mailing list. |
| `triage` | object | yes (or inherited) | Milestones file path, milestone namespace, recognised triage labels, chair-label-authority flag. |

### Inheritance rules

1. **Single-level only.** A config either has `extends: <id>` (referencing exactly one parent) or it does not. No transitive chains. `effective_config = parent + override` is a one-step computation.
2. **Object fields deep-merge.** Specified keys override; unspecified keys inherit.
3. **Array fields fully replace.** Append-style inheritance gets ambiguous (does the parent's lead show up in the child?). Replace is unambiguous.
4. **Scalars override.** Any scalar in the child wins.
5. **`null` in child explicitly clears a parent value.** Distinct from omitting the key (which inherits).
6. **Schema versions must match.** A child cannot extend a different-`schema_version` parent.

### Worked example: `configs/ws4.yaml`

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

### Sketched example for inheritance validation: `configs/adlc.yaml` (v2+)

```yaml
schema_version: 1
extends: ws4

workstream:
  id: adlc
  name: ADLC SIG
  full_name: Security of Agent Development Lifecycle SIG
  parent_workstream: ws4

leads:
  - { name: Kathleen Goeschel, github: null, role: chair }
  - { name: Parul Singh, github: null, role: chair }

meeting:
  cadence: Wednesdays
  time: "11:00 ET / 08:00 PT"
  meeting_minutes_dir: meeting_minutes/adlc
  filename_pattern: "{YYYY}-{MM}-{DD}.md"
  fallback_minutes_dir: meeting_minutes/ws4

# repo, channels, triage all inherited from ws4
```

### `triage_milestones.json` shape

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
          "wave": "Playbook wave 1",
          "milestone": "playbook-v1.0",
          "contents": "The 7 playbooks (#52-#58)"
        }
      ]
    }
  }
}
```

The skill picks the namespace from `config.triage.milestone_namespace`. v1 ships with only the `ws4` namespace populated.

### What the config does NOT carry

- AI attribution convention — that is CoSAI-wide; lives in the manifest's `governance` block (every skill sees it).
- License — same reason.
- Cross-workstream defaults — until 3+ configs share boilerplate, no `_cosai.yaml` base. Adding it later is a clean diff.

---

## 7. `agenda_drafts/` location and frontmatter

Tracked in repo. Mirrors `meeting_minutes/<ws>/` for the *future-meeting* case.

### Path

`agenda_drafts/<workstream>/YYYY-MM-DD.md`

The date is the **meeting date**, not the generation date.

### Frontmatter

The example below shows a draft generated by `sarahnovotny` for the 2026-05-08 WS4 meeting. Values are illustrative — the runtime-populated fields (`generated_at`, `generated_by`, `generated_by_role`) are filled in by the skill on each run, *not* hardcoded. `generated_by` is whoever ran the skill (resolved from the user's `gh` identity); `generated_by_role` is derived from the workstream config's `leads:` array combined with a `gh` permission check.

```yaml
---
schema_version: 1                       # constant: this frontmatter schema's version
workstream: ws4                         # from the skill's argument
meeting_date: 2026-05-08                # the meeting this agenda is FOR
generated_at: 2026-05-07T15:42:00Z      # set at run time
generated_by: sarahnovotny              # set at run time from gh identity
generated_by_role: chair                # derived: configs/ws4.yaml leads + gh permission check
source_skill: cosai-meeting-agenda      # constant per skill
source_skill_version: 1.0.0             # from manifest.version
status: draft                           # initial state
promoted_to: null                       # set after promotion
promoted_at: null                       # set after promotion
supersedes: null                        # set if regenerated
---
```

### Lifecycle states

| State | When set | Meaning |
|---|---|---|
| `draft` | initial generation | freshly generated, not yet reviewed |
| `reviewed` | optional, set when user has read but not yet promoted | parking state |
| `promoted` | after Discussion is created | `promoted_to` + `promoted_at` populated; file stays put |

### Re-run behaviour for same `meeting_date`

- If `status: draft` exists → **overwrite in place**. Git history is the audit trail.
- If `status: reviewed` or `promoted` exists → halt with a message; do not silently overwrite work. User decides whether to delete the prior file or change date.

### Promotion mechanics

When the user explicitly approves promotion:

1. Read the draft file.
2. Strip frontmatter (Discussions don't render YAML frontmatter cleanly).
3. Create the Discussion via `gh api graphql` (gh CLI's discussion support is GraphQL-only).
4. On success, update the draft file's frontmatter: `status: promoted`, `promoted_to: <discussion URL>`, `promoted_at: <now>`.
5. Optionally commit the frontmatter update with the vendor-neutral AI trailer.

### Cleanup

None. Drafts stay indefinitely as audit trail. If the directory grows unwieldy, an `agenda_drafts/<ws>/archive/<year>/` move convention can be added later.

### `.gitignore` implications

The reorg branch's `.gitignore` currently has:

```
.DS_Store
meeting_minutes
.claude
```

`agenda_drafts/` is **tracked**; no `.gitignore` change needed. `CONTRIBUTING.md` gets a one-line note: "agenda drafts are tracked under `agenda_drafts/<workstream>/`; please don't add this path to `.gitignore`."

---

## 8. Renderer (`render.py`)

### CLI surface

```
python scripts/agent/render.py <skill-name> --target=<target> [options]

Targets:
  claude-code   Install for Claude Code in ~/.claude/skills/ (default)
  generic       Emit a generic-prompt rendering (v1: stub, returns "deferred to v2")

Options:
  --config=<workstream>    Resolve a specific workstream config for path substitution.
                           Default: all configs are usable at run time; renderer
                           substitutes the absolute repo path only.
  --output=<path>          Override the destination directory.
                           Default: ~/.claude/skills/ for --target=claude-code.
  --symlink                Symlink files instead of copying (DEFAULT for claude-code).
  --copy                   Copy files (frozen install).
  --dry-run                Validate and print intended actions; do not write.
  --validate-all           Walk scripts/agent/, validate every manifest and config.
                           Returns non-zero on any failure. CI hook.

Examples:
  python scripts/agent/render.py cosai-meeting-agenda --target=claude-code
  python scripts/agent/render.py cosai-issue-triage --target=claude-code --copy
  python scripts/agent/render.py --validate-all
```

### Behaviour: `--target=claude-code`

1. **Load and validate.** Read `manifest.yaml`, validate against `manifest.schema.json`. Read `SKILL.md`. If `--config=<ws>` provided, resolve the config (with one `extends` hop) and check `dependencies.configs` paths exist.
2. **Build Claude Code frontmatter.** Convert manifest fields to Claude Code's required frontmatter:
   ```yaml
   ---
   name: cosai-meeting-agenda
   description: <copied from manifest.description, single-line collapsed>
   ---
   ```
3. **Stitch.** Concatenate frontmatter with the manifest's `narrative` body (SKILL.md, verbatim).
4. **Inject manifest-context block.** After the frontmatter, before SKILL.md prose, emit a YAML-fenced summary of the manifest's contracts so the running model can refer to them without re-parsing manifest.yaml. Example:
   ```markdown
   ## Skill Contract (auto-generated from manifest.yaml; do not edit)

   ```yaml
   arguments: [...]
   dependencies: {tools: [...], configs: [...], data: [...]}
   composition: {...}
   output: {...}
   boundaries: [...]
   ```

   See `scripts/agent/<skill>/manifest.yaml` for canonical.
   ```
5. **Substitute repo paths.** Two kinds of placeholders exist:
   - **Render-time substitution (resolved during install).** The absolute path to `scripts/agent/configs/` and the absolute path to the repo root replace any `<repo_root>/...` references in the rendered SKILL.md. After rendering, the running model can locate configs without knowing where the source repo lives.
   - **Run-time placeholders (preserved verbatim).** The workstream slug (`{workstream}`) and config-field references (`{config.meeting.cadence}`, `{config.meeting.meeting_minutes_dir}`, etc.) stay literal in the rendered SKILL.md. The model resolves these at run time after loading the workstream config the user names as the argument. One install handles WS4, WS3, ADLC, etc.
6. **Place files.** Default destination: `~/.claude/skills/<skill-name>/`. Files placed:
   - `SKILL.md` (the rendered/stitched version)
   - Sibling files declared in manifest as needed at runtime (e.g. `triage_milestones.json` for the triage skill)
   - With `--symlink` (default): symlink targets back to repo files so edits are live.
   - With `--copy`: frozen copy.
7. **Report.** Print what was written, where. Print warnings for any `provisioning.kind: out-of-band` data dependencies (e.g. "Reminder: ensure `meeting_minutes/ws4/` is populated by `scripts/fetch_meeting_minutes.py`").

### Behaviour: `--target=generic` (v1 stub)

Print "Generic-prompt rendering deferred to v2" + the manifest summary. Exit 2. Accepting the flag means the v2 PR is purely additive.

### Behaviour: `--validate-all`

Walks `scripts/agent/`. For every `*/manifest.yaml`: validate against `manifest.schema.json`. For every `configs/*.yaml`: validate against `_config.schema.json` and check that `extends` references resolve. Returns non-zero on any failure. Designed for `pre-commit` and CI gate.

### Implementation choices

- **Python 3.12+.** Existing skill in shared `~/Github/python3.12-venv/`.
- **Deps:** `pyyaml`, `jsonschema`. Both pip-installable, both already present in the shared venv. No `click`/`typer` — `argparse` is fine.
- **Single file:** `render.py`, target ~150-250 LOC.
- **No state files. No caching.** Every run reads canonical sources fresh.
- **Atomic file writes:** write to a tempfile, rename. Avoids half-written output.

### What the renderer does NOT do

- Does not fetch from the network.
- Does not modify the source manifest or SKILL.md (read-only on the source).
- Does not auto-install dependencies (`gh`, `pyyaml`, etc.). Fails fast with install instructions if missing.
- Does not manage Claude Code's session lifecycle. Once installed, Claude Code discovers the skill on its own.

---

## 9. Migration approach

The existing `agenda` and `triage` skills (in `cosai-claude/skills/` and locally as `.bak`) keep working. New `cosai-meeting-agenda` and `cosai-issue-triage` are added in parallel under `scripts/agent/`. Coexistence is intentional — the user decides when to switch their workflow.

### Per-skill mechanics

For each skill (`agenda` → `cosai-meeting-agenda`, `triage` → `cosai-issue-triage`):

1. **Split the existing SKILL.md** into:
   - `manifest.yaml` — extract contracts, dependencies, boundaries, failure modes, output shape.
   - `SKILL.md` — keep the imperative process narrative verbatim, with three categories of edits:
     - Replace hardcoded WS4 values with config references: `Thursdays 12:00 ET` → `{config.meeting.cadence} {config.meeting.time}`.
     - Replace hardcoded paths with config references: `meeting_minutes/` → `{config.meeting.meeting_minutes_dir}/`.
     - Replace inline data-source descriptions with manifest pointers: "fetched nightly from Google Drive by `~/Github/scripts/fetch_meeting_minutes.py`" becomes a single sentence pointing at `manifest.yaml`'s `dependencies.data[0].provisioning` block.

2. **Move WS4-specific data into `configs/ws4.yaml`:**
   - Lead names, GitHub handles, roles → `leads:`
   - Slack channel, mailing list → `channels:`
   - Discussion #84 → `meeting.agenda_template_discussion`
   - Meeting cadence + time → `meeting.cadence` + `meeting.time`
   - Filename pattern → `meeting.filename_pattern`

3. **Triage-specific:**
   - `triage_metadata.json` content moves to `triage_milestones.json` under `namespaces.ws4.milestones`.
   - SKILL.md's reference to "`triage_metadata.json` in this skill's directory" becomes a reference to `triage_milestones.json` with namespace from `config.triage.milestone_namespace`.

4. **Path substitution at render time:** When `render.py --target=claude-code` installs, it substitutes the absolute path to `scripts/agent/configs/` into the rendered SKILL.md. The workstream slug stays as a runtime argument (preserving the current "argument-driven" UX where one install handles WS4, WS3, ADLC, etc.).

5. **Behaviour parity check.** Before retiring anything, run the new skill against a known-good case and compare output:
   - **Agenda parity:** generate a draft for the most recent past WS4 meeting, diff against the actual posted Discussion (or the existing skill's draft for the same week).
   - **Triage parity:** run on a recently-triaged issue, compare to @parmarmanojkumar's actual triage note for that issue.

   Not byte-equality — formatting may shift slightly with path substitution and manifest references. Should be **semantic equality**: same recommendations, same milestone choices, same action item carryovers. Document the comparison in the migration PR.

### Parallel-coexistence period

Both old (`agenda`, `triage`) and new (`cosai-meeting-agenda`, `cosai-issue-triage`) can be installed in `~/.claude/skills/` simultaneously. Different names, both surfaced in available-skills list. User invokes whichever they want.

Recommended sequence:
- Week 1: ship migration PR. Use new skills for low-stakes runs.
- Weeks 2-3: use new skills as primary; keep old as fallback. Note any behaviour gaps.
- Week 4+: if happy, stop using old skills (they keep working in cosai-claude; nothing to remove in this repo).

### CLAUDE.md update

The project CLAUDE.md is updated to describe **only** the new pathway (`scripts/agent/` via `render.py --symlink`). The legacy `.claude/skills.bak/` pathway is noted as deprecated locally — kept for reference only.

### Documentation deliverables in v1 PR

- `scripts/agent/README.md` — what `scripts/agent/` is, how to install via `render.py`, links to `MANIFEST_SCHEMA.md` and the worked example.
- `scripts/agent/MANIFEST_SCHEMA.md` — human-readable manifest field reference (every field with type, required/optional, semantics).
- A 1-paragraph blurb in `CONTRIBUTING.md` (under a new "Working with WS4 tooling" section) pointing at `scripts/agent/README.md`.

### Bundled tooling sync

The v1 PR also syncs `scripts/fetch_meeting_minutes.py` to its current production version (the `~/Github/scripts/` working copy includes WS3 + Code-SIG + RM-SIG sources and the `HttpError`-resilient export path; the repo copy at the time of writing is the older Apr 20 version). The manifest's `provisioning.populated_by.tool` points at this in-repo path; a stale copy would contradict the contract. Sync is bundled here rather than in a separate PR because the agent-skills migration relies on the script's WS3+SIGs ability to populate `meeting_minutes/` for non-WS4 workstreams.

---

## 10. Validation and testing

### Schema validation

- `manifest.schema.json` and `_config.schema.json` are JSON Schema 2020-12.
- `render.py --validate-all` runs every manifest and config through validation. Exits non-zero on any failure.
- CI gate (GitHub Actions or pre-commit) runs `--validate-all` on every PR that touches `scripts/agent/`.

### Behaviour parity tests

For each migrated skill, the migration PR includes a "parity report" describing:

- The known-good input case (date-stamped agenda or specific issue number)
- The old-skill output (committed as a reference snapshot under the parity report so future readers can verify the comparison)
- The new-skill output
- The semantic-equality assessment (same recommendations, same milestone choices, same carryovers — even if formatting/wording shifts)
- Any deltas, with a one-line explanation per delta

These reports are committed under `scripts/agent/parity-reports/<skill>-<date>.md` for posterity.

### Renderer self-test

`render.py --dry-run cosai-meeting-agenda --target=claude-code` exits 0 and prints intended actions. Used as a smoke test.

### What is NOT tested in v1

- End-to-end "agenda generated and promoted to a real Discussion." That requires a live test repo or careful staging; deferred until v2 when more workstream configs exist and the value of automation is higher.
- Phase 3 composition. Not implemented in v1.
- Generic-prompt rendering. Not implemented in v1.

---

## 11. Acceptance criteria for v1

The v1 PR is ready to merge when:

1. `scripts/agent/` exists with the directory layout in §4.
2. `manifest.schema.json` and `configs/_config.schema.json` validate the worked examples.
3. `MANIFEST_SCHEMA.md` documents every field in §5 and §6.
4. `cosai-meeting-agenda/manifest.yaml` and `cosai-meeting-agenda/SKILL.md` exist; `render.py cosai-meeting-agenda --target=claude-code --dry-run` exits 0.
5. `cosai-issue-triage/manifest.yaml`, `cosai-issue-triage/SKILL.md`, and `cosai-issue-triage/triage_milestones.json` exist; renderer dry-run exits 0.
6. `configs/ws4.yaml` exists and validates.
7. `render.py --validate-all` exits 0 with all v1 artefacts in place.
8. Parity reports are committed for both migrated skills, documenting semantic equality with the legacy `.bak` versions on at least one recent real-world input each.
9. `scripts/agent/README.md` walks a fresh user through install + first-run.
10. `CONTRIBUTING.md` has a one-paragraph pointer to `scripts/agent/README.md`.
11. Project `CLAUDE.md` is updated to describe only the new pathway.
12. `agenda_drafts/` directory exists with at least a `.gitkeep` or a placeholder README explaining the convention.
13. CI gate runs `render.py --validate-all` on PR.
14. `scripts/fetch_meeting_minutes.py` is updated to its current production version (with WS3 + Code-SIG + RM-SIG drive sources and the `HttpError`-resilient export path). The in-repo copy must match what the manifest's `provisioning.populated_by.tool` points at; a stale copy contradicts the contract.

---

## 12. Open items deferred to v2 or later

- Workstream configs for WS3, ADLC, RM-SIG, Code-SIG (drop-in PRs after schema settles).
- Generic-prompt renderer (`render.py --target=generic`).
- Phase 3 composition implementation: `cosai-meeting-agenda` invokes `cosai-issue-triage` inline for unlabeled issues. Chair-permission-gated update flow per Decision #4. Manifest already declares the composition in `composition.calls`.
- A CoSAI-wide `_cosai.yaml` base config (added when 3+ workstream configs share boilerplate).
- Deprecation of `sarahnovotny/cosai-claude/skills` (left alone for now).
- Migration of `fetch_meeting_minutes.py` into `scripts/agent/` (out of scope; lives separately as a per-host sync tool).
- Codex and Gemini CLI renderers (PRs from people who use those harnesses).

---

## 13. Provenance

This design was developed via brainstorming session on 2026-05-08, AI-assisted (Claude Code, Opus 4.7). Sarah Novotny directed the design through 6 rounds of design questions; AI structured the choices, drafted text, and applied iterative direction. Sarah reviewed and approved each section.

Per CoSAI vendor-neutral attribution convention, the commit landing this document uses:

```
Co-authored-by: AI Assistant <ai-assistant@coalitionforsecureai.org>
```

Per WS4 CONTRIBUTING.md AI Usage Policy, this PR's body discloses the substantial AI assistance with tool name and stage of drafting.
