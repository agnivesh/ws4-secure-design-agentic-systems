# WS4 agent skills

Self-contained agent definitions for repeatable WS4 program-management tasks.
Each skill is a folder with a `SKILL.md` (name + description frontmatter, then
instructions), usable with any LLM assistant. Workstream specifics (repo, leads,
cadence, recognised labels, milestones) live in tables inside each `SKILL.md`.

| Skill | What it does |
|-------|--------------|
| [`meeting-agenda`](meeting-agenda/SKILL.md) | Drafts an agenda for an upcoming CoSAI workstream/SIG meeting from minutes + open issues/PRs. Draft only — promotion to a Discussion is approval-gated. |
| [`issue-triage`](issue-triage/SKILL.md) | Produces a structured triage note for an issue/PR in @parmarmanojkumar's format. Never posts without approval. |

## Installing

Install into your agent with the [`skills` CLI](https://github.com/vercel-labs/skills).
These live under `scripts/agents/` (a custom location), so use the direct
subfolder URL:

```bash
# meeting-agenda
npx skills@latest add https://github.com/cosai-oasis/ws4-secure-design-agentic-systems/tree/main/scripts/agents/meeting-agenda

# issue-triage
npx skills@latest add https://github.com/cosai-oasis/ws4-secure-design-agentic-systems/tree/main/scripts/agents/issue-triage
```

The `meeting-agenda` skill reads meeting minutes synced by
[`scripts/fetch_meeting_minutes.py`](../fetch_meeting_minutes.py) (setup in
[`scripts/README.md`](../README.md)).
