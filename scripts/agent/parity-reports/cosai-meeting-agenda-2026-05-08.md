# cosai-meeting-agenda — parity report (2026-05-08, scaffold)

**Goal:** Verify the migrated `cosai-meeting-agenda` skill produces semantically equivalent output to the legacy `agenda` skill for a known-good input.

**Status:** scaffold — v1 acceptance criterion #8 deliverable. Populated content (actual diff comparison) lands once Sarah invokes the migrated skill against a real WS4 meeting and captures both the legacy and migrated outputs.

## Reproduction steps

```bash
# 1. Install the new skill (symlink mode by default).
python scripts/agent/render.py cosai-meeting-agenda --target=claude-code

# 2. Ensure meeting_minutes/ws4/ is current.
python scripts/fetch_meeting_minutes.py --skip-existing

# 3. Optionally keep the legacy `agenda` skill installed in parallel for direct comparison.
#    The legacy lives in cosai-claude/skills/agenda/ — install via that repo's instructions.

# 4. In Claude Code:
#    > Use cosai-meeting-agenda with workstream ws4
#
#    The new skill writes a draft to:
#    agenda_drafts/ws4/<next-meeting-date>.md

# 5. Optionally invoke the legacy skill the same way and capture its inline output.
```

## Input case

- Workstream: WS4
- Meeting date: (TBD — fill in when running)
- Reference: most recent posted agenda Discussion as the canonical "what good looks like"

## Old-skill output (reference snapshot)

> Pasted verbatim from the most recent posted Discussion (or from a captured legacy-skill run for the same week, if both are installed in parallel).

```markdown
<paste here>
```

## New-skill output

> Pasted verbatim from `agenda_drafts/ws4/<date>.md`, including frontmatter.

```markdown
<paste here>
```

## Semantic equivalence assessment

| Section | Old | New | Match? | Notes |
|---|---|---|---|---|
| Action Item Follow-ups | <count> items | <count> items | ✓ / ✗ | Same owners, same items? |
| PRs Needing Review | <count> PRs | <count> PRs | ✓ / ✗ | |
| Issues Needing Chair Decision | <count> | <count> | ✓ / ✗ | |
| New Issues Since Last Meeting | <count> | <count> | ✓ / ✗ | |
| Cross-Stream Updates | <count> | <count> | ✓ / ✗ | |

## Expected deltas (informational; fill in actual on first run)

The migrated skill is expected to differ from the legacy in the following ways. These are deliberate and do NOT count as parity failures:

- **Frontmatter present in new only.** The new skill writes a tracked `agenda_drafts/<ws>/<date>.md` file with YAML frontmatter (`schema_version`, `workstream`, `meeting_date`, `generated_at`, `generated_by`, `status`, etc.); the legacy skill produced inline output only.
- **WS4 lead names externalised.** "Sarah Novotny, Ian Molloy" no longer appears as a hardcoded string in the body — those values come from `configs/ws4.yaml`'s `leads:` and are referenced as `{config.leads}` in the SKILL.md, resolved at run time.
- **`{config.X}` references resolved at run time.** The new skill's prose contains placeholders like `{config.meeting.cadence}` that the model resolves against the loaded workstream config; the legacy hardcoded these values.
- **Unlabeled-issue triage embedded inline (Phase 3, deferred).** The legacy skill simply listed unlabeled issues in a "needs triage" table. The new skill v1 does the same. The Phase 3 composition (calling `cosai-issue-triage` inline) is declared in `manifest.yaml` `composition.calls` but not implemented in v1.

## Verdict (fill in on first run)

- [ ] Semantically equivalent. Migration parity confirmed for this case.
- [ ] Discrepancies found requiring follow-up. Detail below.

## Follow-up items (fill in on first run)

(List any unexpected deltas or behaviour changes that warrant a follow-up issue or PR.)
