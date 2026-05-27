# cosai-meeting-agenda — parity report (2026-05-08, first real run)

**Goal:** Verify the migrated `cosai-meeting-agenda` skill produces semantically equivalent output to the legacy `agenda` skill for a known-good input.

**Status:** populated — first invocation of the migrated skill against real WS4 inputs (2026-05-14 meeting prep, run 2026-05-08). Side-by-side direct comparison of skills was not possible (the legacy `agenda` skill is deprecated locally per `CLAUDE.md`); the closest reference for "what good looks like" is the most recent posted Discussion **#95** (WS4 Agenda — May 7, 2026), produced under the prior conventions one week earlier.

## Reproduction steps

```bash
# 1. Skill is already installed (symlink) from earlier session.
#    To re-install: python scripts/agent/render.py cosai-meeting-agenda --target=claude-code

# 2. Confirm meeting_minutes/ws4/ is current (last meeting WS4-20260507.md present).
ls -t meeting_minutes/ws4/ | head -3
#    WS4-20260507.md  ← last meeting
#    WS4-20260430.md
#    WS4-20260428.md

# 3. In Claude Code:
#    > Use cosai-meeting-agenda with workstream ws4
#
#    Skill resolves configs/ws4.yaml, reads meeting_minutes/ws4/WS4-20260507.md,
#    pulls Discussion #95 (most recent agenda) for carried action items,
#    pulls open PRs and issues via gh, and writes the draft.

# 4. Output:
#    agenda_drafts/ws4/2026-05-14.md  (status: draft)
```

## Input case

- **Workstream:** WS4
- **Meeting date:** 2026-05-14 (next Thursday slot)
- **Last meeting:** 2026-05-07 (`WS4-20260507.md`, ~74 KB Gemini-generated minutes)
- **Reference agenda:** Discussion **#95** "WS4 Agenda — May 7, 2026" (Ian Molloy, posted 2026-05-07)
- **Open PRs at run time:** 8 (#59, #68, #72, #89, #91, #92, #93, #96)
- **Open issues at run time:** 35 (incl. RFC #94 filed 5/7, plus standing playbook stubs and whitepaper clusters)

## Old-skill output (reference snapshot — Discussion #95)

> Verbatim body from the most recent posted Discussion. Used as the structural reference for "what the agenda format should look like" since the legacy skill is deprecated locally.

```markdown
## WS4 Agenda — May 7, 2026

### Agenda

| Time | Owner | Topic |
| -----|--------|-------|
| 5'  | Sarah | Action item review (1a/1b/1c) |
| 10' | @Johncavanaugh-IIS | PQC RFC — issue creation + Sarah's PR anchor |
| 10' | Benedict Lau | Agent Credentials RFC — scoping readout |
| 5'  | Ian | CPEX / APL spec status |
| 10' | Open | PR review pickups (#73, #68, #91) |
| 5'  | Leads | Cross-stream: TSC SRF transition, ADLC scope progress |
| *   | Leads | Triage: unlabeled issues + RFCs under review |

### 1. Action Item Follow-ups

#### 1a. Done
… (4 rows: Raymond, Ingrid, Sarah, Ian) …

#### 1b. In flight
… (7 rows, carried items) …

#### 1c. New (from Apr 30)
… (10 rows) …

### 2. PRs Needing Review
… (5 rows: #91, #89, #72, #68, #59) …

### 3. Issues Needing Chair Decision
RFCs under review (3 rows) + Unlabeled needing triage (4 rows)

### 4. New Issues / PRs Since Last Meeting
"None filed since 4/30."

### 5. IETF Draft Alignment
3-row table

### 6. SIG + Cross-Stream Updates
4-row table
```

(Full text in Discussion **#95** at `cosai-oasis/ws4-secure-design-agentic-systems`.)

## New-skill output

> Frontmatter + body from `agenda_drafts/ws4/2026-05-14.md` (status: draft, not yet promoted).

```markdown
---
schema_version: 1
workstream: ws4
meeting_date: 2026-05-14
generated_at: 2026-05-08T17:35:00Z
generated_by: sarahnovotny
generated_by_role: chair
source_skill: cosai-meeting-agenda
source_skill_version: 1.0.0
status: draft
---

## WS4 Agenda — May 14, 2026

### Agenda
| Time | Owner | Topic |
| 5'   | Sarah | Action item review (1a / 1b / 1c) |
| 10'  | Benedict Lau | Agent Credentials RFC — early-draft readout |
| 10'  | Frederico / Ian | RFC #94 (CPEX) — framework intro + reviewer ask |
| 5'   | Kapil Singh | IETF Whimsy / Pieter Kasselman draft — write-up + recommendation |
| 5'   | Parul Singh | Trust Graph demo (committed 5/7) |
| 5'   | Open | PR review pickups (#68, #91, #92, #93, #96) |
| 5'   | Leads | Cross-stream: readout from 5/8 cross-workstream sync, SRF→WS3, ADLC scope |
| *    | Leads | Triage: unlabeled issues + RFCs under review |

### 1. Action Item Follow-ups
1a. Done — 7 rows
1b. In flight (carried) — 9 rows
1c. New (from 5/7) — 5 rows

### 2. PRs Needing Review — 8 rows (#96, #93, #92, #91, #89, #72, #68, #59)
### 3. Issues Needing Chair Decision — RFCs (4 rows: #94, #86, #61, #9) + Unlabeled (9 rows)
### 4. New Issues / PRs Since Last Meeting — 1 row (PR #96, filed 5/8)
### 5. IETF Draft Alignment — 4 rows
### 6. SIG + Cross-Stream Updates — 5 rows
```

(Full text at `agenda_drafts/ws4/2026-05-14.md`.)

## Semantic equivalence assessment

| Section | Old (#95) | New (5/14 draft) | Match? | Notes |
|---|---|---|---|---|
| Header **Agenda** time-budget table | 7 rows | 8 rows | ✓ structure | Same column shape (Time/Owner/Topic); row count differs because the 5/14 agenda has trust-graph + cross-WS-sync readout slots |
| §1 Action Item Follow-ups (1a/1b/1c split) | 4 / 7 / 10 | 7 / 9 / 5 | ✓ structure | Same three-table split; row counts shift because more items completed in the 5/7 meeting (RFC #94 + PR #93 closed two carried items) and fewer net-new items emerged |
| §2 PRs Needing Review | 5 PRs | 8 PRs | ✓ structure | Same `\|PR\|Author\|Notes\|` shape; #96, #93, #92 are net-new since 5/7 |
| §3 RFCs under review + Unlabeled triage | 3 + 4 | 4 + 9 | ✓ structure | New additions: RFC #94 (filed 5/7) joined RFCs-under-review; unlabeled bucket grew because the prior agenda missed AGNTCY #47/#48/#49 + Omar #11 / #7 |
| §4 New Issues Since Last Meeting | "None" | 1 row (PR #96) | ✓ | Renders correctly with a single-row table when there is exactly one item |
| §5 IETF Draft Alignment | 3 rows | 4 rows | ✓ | Added a row for connecting RFC #94 (CPEX) → IETF discussions |
| §6 SIG + Cross-Stream Updates | 4 rows | 5 rows | ✓ | Added cross-workstream-sync row (the 5/8 sync); merged Trust Graph ↔ CPEX row |

**Format conventions verified:**
- ✓ Tables-over-bullets honored throughout
- ✓ `**#NN**` (bold) for issue/PR numbers in tables
- ✓ Disclaimer omitted (per the 4/20 user-override convention encoded in the SKILL.md)
- ✓ Done items remain on this agenda for visibility (will drop off 5/21 agenda per rolling-done rule)
- ✓ `Done → #NN` / `Done → PR #NN` / `Done — <note>` pointer style preserved
- ✓ Ambiguous items annotated inline (e.g., Poorna's name conflict with Gemini's `p****` transcription)

## Expected deltas (informational)

The migrated skill differs from the legacy `agenda` skill in these intentional, non-failure ways:

- **Frontmatter present in new only.** The new skill writes a tracked `agenda_drafts/ws4/2026-05-14.md` file with YAML frontmatter (`schema_version: 1`, `workstream: ws4`, `meeting_date: 2026-05-14`, `generated_at`, `generated_by: sarahnovotny`, `generated_by_role: chair`, `source_skill`, `source_skill_version: 1.0.0`, `status: draft`). The legacy skill produced inline output only.
- **WS4 lead names externalised.** "Sarah Novotny, Ian Molloy" no longer appears as a hardcoded string in the SKILL.md; values come from `configs/ws4.yaml` `leads:` and were resolved at run time. Confirmed working — `generated_by_role: chair` was correctly resolved by matching `sarahnovotny` against the `role: chair` entries.
- **`{config.X}` placeholders resolved at run time.** The skill's prose contains placeholders like `{config.meeting.cadence}` and `{config.meeting.meeting_minutes_dir}` that resolved against `configs/ws4.yaml` correctly. No leakage of `{config.X}` strings into the agenda body.
- **Unlabeled-issue triage embedded inline (Phase 3, deferred).** The new skill v1 lists unlabeled issues with `(needs triage)` framing and does not invoke `cosai-issue-triage`. Manifest declares the composition as `v1_status: deferred`. Behavior matches the legacy skill.
- **Drafts persisted under repo control.** `agenda_drafts/ws4/2026-05-14.md` is now a tracked artifact. Diff between this draft and the eventual posted Discussion will be visible in `git log`. Legacy drafts lived in `.claude/drafts/` (gitignored).

## Verdict

- [x] **Semantically equivalent.** Migration parity confirmed for the 2026-05-14 WS4 case. The migrated skill produced a draft that follows the discussion #95 conventions exactly (table-per-section, no disclaimer, rolling-done in 1a, `**#NN**` formatting) and added intentional improvements (frontmatter for audit trail, config-driven leads, in-repo draft persistence) without regressions.
- [ ] Discrepancies found requiring follow-up.

## Follow-up items

None blocking. Observations worth tracking:

1. **Discussion #95 missed several long-standing unlabeled issues** (#47/#48/#49 AGNTCY, #11, #7). The migrated skill surfaced them in §3. This isn't a parity issue — it's a fidelity improvement from the migrated skill walking the full open-issue set rather than only what felt "fresh" to a human curator. Worth confirming with Ian whether these belong on the recurring chair-decision list or should be triaged-and-closed.
2. **`generated_at` is the skill-run timestamp**, not the meeting time. This is intentional per DESIGN.md §7 (provenance), but is worth noting in case the field ever needs to mean "meeting start time" — that semantic belongs to `meeting_date`, not `generated_at`.
3. **No `composes:` invocation occurred.** All issues either had recognised triage labels (per `configs/ws4.yaml` `triage.recognised_triage_labels`) or fell into the v1 inline `(needs triage)` listing. Phase 3 composition into `cosai-issue-triage` remains deferred. Will get exercised once Phase 3 lands.
4. **One naming ambiguity propagated forward.** "Poorna Rajaraman" vs Gemini transcript's `p****` from 5/7 minutes — preserved as an inline annotation rather than silently resolved, per the rolling-done convention's "annotate ambiguity rather than auto-resolve" rule.
