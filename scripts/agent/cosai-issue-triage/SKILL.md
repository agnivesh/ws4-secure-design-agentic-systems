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
