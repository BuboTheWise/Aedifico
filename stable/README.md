# Toolbox — Stable Skills Index

This directory contains production-ready skills shared across all Hermes agents. Each skill has:
- **SKILL.md** — spec, usage docs, cron template, success criteria
- **config/** — user-editable configuration (JSON)
- **scripts/** — executable implementation (Python)

## Installing a Skill

To make a skill available to your profile's sessions:

```bash
hermes skills install /home/stefan/Projects/Toolbox/stable/<skill-name>/SKILL.md
```

Or symlink if you prefer local development access:
```bash
ln -s /home/stefan/Projects/Toolbox/stable/<skill-name> ~/.hermes/skills/<skill-name>
```

## Available Skills

| Skill | Purpose | Cron? |
|-------|---------|-------|
| `memchorus-pr-collab` | Work intake + PR responsiveness (bugs, issues, open PRs) | Yes |
| `pr-comment-monitor` | Monitor third-party PR review comments needing replies | Yes |
| `development-process` | Atomic card workflow (spec-first, QA gates, git ops) | No |
| `team-dev-process` | Team dev process conventions and coordination | No |
| `sdlc-review` | Review Kanban handoffs and route verified outcomes | No |
| `mentorship` | Bidirectional teaching protocol between agents | No |

## Adding a New Skill

1. Create `stable/<skill-name>/SKILL.md` following the pr-comment-monitor format
2. Add config if needed in `config/` subdirectory
3. Add implementation scripts in `scripts/` subdirectory
4. Update this index file
5. Install to profiles that need it: `hermes skills install stable/<skill-name>/SKILL.md`

## Maintenance

- PRs should update the skill with a version bump and changelog entry
- All agents should sync their local skills monthly or when notified of updates
- Breaking changes require agent migration plan in the PR description
