# Toolbox — Shared Development Skills for Hermes Agent

Canonical repository of reusable, importable skills for every Hermes Agent profile.

## Overview

This repo hosts shared development process skills that any Hermes profile can load to standardize their workflow — task structure, QA separation, git discipline, and iterative improvement patterns.

Skills are distributed as `skills/<name>/SKILL.md` files. Each skill is self-contained: proper frontmatter, When/How/Verification sections, and no external dependencies beyond the Hermes Agent runtime.

## Skills

### development-process

**Purpose:** Standardize task workflow, phases, QA separation, and git-first discipline for all Hermes profiles.

**Coverage:**
- Kanban task structure (Objective, Criteria, Testing, Verification)
- Six-phase development workflow (Preparation → Code Quality → Feature Implementation → QA Review → Documentation → Iterative Improvement)
- Git discipline (conventional commits, push rules)
- QA protocols (review separation, review checklist)
- Session logging (session log format)

**Import this skill by:**
1. **Via `skill_view` tool** — call `skill_view(name='development-process')` after installing the skill to your profile
2. **Via collective-wisdom plugin** — add this repo as a collective-wisdom source in your config
3. **Direct path** — clone and reference `skills/development-process/SKILL.md` directly

## Install for Your Profile

### Option A: skill_manage (recommended)

Add to your profile's installed skills or use the collective-wisdom plugin to pull from this repo.

### Option B: Clone locally

```bash
git clone https://github.com/BuboTheWise/Toolbox.git ~/.hermes/toolbox
# Then symlink or copy skills into your profile
ln -s ~/.hermes/toolbox/skills ~/your-profile/skills/toolbox
```

### Option C: Add to config.yaml

In your profile's `config.yaml`, add this repo as a skill source under the `skills` section so it loads automatically.

## Contributing Skills

1. Follow the [Hermes Agent Skill Authoring Standard](https://hermes-agent.nousresearch.com/docs/)
2. Use proper SKILL.md frontmatter (name, description ≤60 chars, version, author, platforms)
3. Include When to Use / Prerequisites / Procedure / Verification sections
4. No machine-local paths in committed files
5. One concern per skill — create a new skill rather than extending existing ones narrowly

## Repo Structure

```
Toolbox/
├── README.md
└── skills/
    ├── development-process/
    │   └── SKILL.md          # Task workflow, phases, QA, git discipline
    └── [future-skills]/
        └── SKILL.md
```

## License

MIT. See each skill's frontmatter for its individual license and author credits.
