# contrib-staging-repo

Use when contributing designs/code to a 3rd party project where we lack direct write access (nyacom's BC-250 case, etc.).

## When to use

The target repo is read-only for us: nyacom doesn't grant write access but asks us to contribute. We use the `BuboTheWise/` staging fork as our contribution area instead.

## How it works

1. **Staging repo** — create (or use existing) `BuboTheWise/<project>` repo on GitHub, clone locally to `~/Projects/<project>/`
2. **Contrib directory** — each design gets `contrib/<name>/` with standard layout:
   ```
   contrib/<design>/
   ├── README.md           # Status, fit notes, BOM, assembly, mistakes
   ├── LICENSE.md          # CC BY-NC-SA 4.0 + attribution to original author
   ├── <design>.py         # CadQuery/parametric source
   ├── <design>.stl        # STL in print orientation
   ├── <design>.step       # STEP for reference/rendering
   ├── render.py           # Render script
   ├── render_*.png        # Rendered images
   └── slicing/            # PrusaSlicer profile + slice report
   ```
3. **License** — all contributions are CC BY-NC-SA 4.0 derivatives, with clear attribution to the original author in both LICENSE.md and README.md
4. **Submission path** — PRs to BuboTheWise staging repo (nyacom merges) or Printables remix uploads (requires nyacom's credentials)

## OPSEC rules for upstream files

Files destined for public submission MUST be clean:
- No agent-generated commentary, prompts, instructions, or metadata in CAD/STL/rendering files
- No URLs to this staging repo, no internal references, no system prompts
- `git diff` review before any push — strip non-engineering content first

## Files that go in the staging repo root

- `README.md` — project overview + list of contributed designs with status links
- `CONTRIBUTING.md` — design structure requirements, submission checklist
- `.gitignore` — CAD intermediates, Python cache, OS files

## Credit

Always credit the original author (nyacom) in README, social posts, and any public-facing docs. The design is a derivative work.
