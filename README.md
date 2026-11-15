# Toolbox — Importable Hermes Development Skills

Central repository for shared, versioned development skills used across Hermes Agent profiles (Bubo, an agent profile, an agent profile, an agent profile, etc.).

## Purpose

Every skill in this repo follows [Hermes Agent skill authoring standards](https://hermes-agent.nousresearch.com/docs) and the team's **Development Workflow Procedure** (source: the team docs vault, `Vault/System/development workflow procedure.md`). Skills are seeded here so all profiles can adopt a consistent, shared baseline rather than diverging independently.

## Directory Structure

```
stable/                     # All canonical, team-approved skills
  <skill-name>/
    SKILL.md                # Frontmatter + body per hermes-agent standards
LICENSE
README.md
```

Future additions will follow the same pattern (e.g., `stable/project-organization/SKILL.md`).

## How to Import a Skill

### Option A: Direct file copy

1. Copy the desired skill directory from this repo into your profile's skills tree:
   ```bash
   cp -r stable/<skill-name> ~/.hermes/skills/optional-skills/<category>/<skill-name>/
   ```
2. The skill will be available on next Hermes session start.

### Option B: Git submodule (recommended for shared sync)

```bash
cd ~/.hermes/skills/
git submodule add https://github.com/BuboTheWise/Toolbox.git toolbox
mkdir -p optional-skills/<category>
ln -s "$HOME/.hermes/skills/toolbox/stable/<skill-name>" "optional-skills/<category>/<skill-name>"
```

### Option C: Load in-session

Once the skill is in your skills tree (Option A or B), load it by name in an active session:
```
skill_view(name='development-process')
```

## Current Skills

| Skill | Path | Description |
|-------|------|-------------|
| development-process | `stable/development-process/SKILL.md` | Canonical development workflow, task structure, and collaboration standards. |

***REMOVED***

All skill content is derived from the team docs vault (`Vault/System/development workflow procedure.md`). Where this repo diverges from the vault, the vault takes precedence — changes here should be tracked back to vault updates.

## Contributing

Skills are seeded by consensus (per the team's Kanban process). To add a new skill:
1. Create it on a branch following SKILL.md authoring standards.
2. Open a PR; review against the `hermes-agent-skill-authoring` hardline requirements.
3. Merge to `main` after approval.

---

*First seed: 2026 — development-process canonical development workflow*
