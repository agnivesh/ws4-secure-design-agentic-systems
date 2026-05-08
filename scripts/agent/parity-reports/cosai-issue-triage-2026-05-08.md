# cosai-issue-triage — parity report (2026-05-08, scaffold)

**Goal:** Verify the migrated `cosai-issue-triage` skill produces semantically equivalent output to @parmarmanojkumar's manual triage format.

**Status:** scaffold — v1 acceptance criterion #8 deliverable. Populated content lands once Sarah invokes the migrated skill against a recently-triaged WS4 issue and captures the comparison.

## Reproduction steps

```bash
# 1. Install the new skill (symlink mode by default).
python scripts/agent/render.py cosai-issue-triage --target=claude-code

# 2. Identify a recently-triaged WS4 issue with a triage comment by @parmarmanojkumar.
gh issue list --repo cosai-oasis/ws4-secure-design-agentic-systems \
  --search 'commenter:parmarmanojkumar' --limit 5 \
  --json number,title,updatedAt

# 3. In Claude Code:
#    > Use cosai-issue-triage with workstream ws4 and issue_number <NN>
#
#    The skill returns a triage note in chat. Capture it verbatim.

# 4. Compare to @parmarmanojkumar's actual comment on issue #NN:
gh issue view <NN> --repo cosai-oasis/ws4-secure-design-agentic-systems --comments
```

## Input case

- Workstream: WS4
- Issue: #<NN> (TBD — fill in when running)
- Reference: @parmarmanojkumar's actual triage comment, dated YYYY-MM-DD

## Reference triage (from @parmarmanojkumar's comment)

> Pasted verbatim from the issue comment.

```
<paste here>
```

## New-skill triage output

> Pasted verbatim from the skill's chat output.

```
<paste here>
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
| Reasoning length | N sentences | M sentences | ✓ if both 2-4 |

## Expected deltas (informational; fill in actual on first run)

- **Milestone reference path.** The new skill resolves milestones from `<repo_root>/scripts/agent/cosai-issue-triage/triage_milestones.json` under `namespaces.ws4.milestones` instead of the legacy flat `triage_metadata.json`. Same content, different file shape.
- **Workstream-aware label set.** The new skill reads `config.triage.recognised_triage_labels` from `configs/ws4.yaml` instead of having the WS4 label set hardcoded.
- **Phase 3 issue-update flow stub.** The new SKILL.md has a "Phase 3 issue-update flow (deferred to v2)" section documenting the chair-permission-gated update flow; this is declarative, not behavioural in v1. The legacy skill never had this section.

## Verdict (fill in on first run)

- [ ] Semantically equivalent. Migration parity confirmed for this case.
- [ ] Discrepancies found requiring follow-up. Detail below.

## Follow-up items (fill in on first run)
