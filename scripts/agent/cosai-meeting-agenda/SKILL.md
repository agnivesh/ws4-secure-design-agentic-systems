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

1. Read the workstream config: `<repo_root>/scripts/agent/configs/{workstream}.yaml`.
2. If the config has `extends:`, merge it onto the named parent config (single-level only) — values in the child override the parent.
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

7. **Write the draft to `<repo_root>/agenda_drafts/{workstream}/{meeting_date}.md`.** Frontmatter per the contract in `<repo_root>/agenda_drafts/README.md`. The fields `generated_at`, `generated_by` (gh identity), `generated_by_role` (looked up from `{config.leads}` plus a `gh` permission check) are populated automatically.

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
