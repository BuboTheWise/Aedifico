# Card Chain Bodies Template v0.1.7

This template encodes the atomic card pattern used across all Hermes profile cards on this project. It ensures every card meets the [development-process](../../development-process/SKILL.md) and [team-dev-process](../SKILL.md) standards without reinventing the wheel.

## Pattern

Every atomic card should contain these four elements:

1. **Objective** — What work is being done? (single sentence, verifiable from a diff or command output)
2. **Success Criteria** — How do we know it's done? (checkable condition)
3. **Required Testing** — How will the team verify it works? (tests to run, where and when)
4. **Verification Steps** — What must be pasted on the card before closing? (real output from tools)

## Example Card Body

```markdown
### Objective

<single sentence describing the exact change>

### Success Criteria

<checkable condition: git status clean, test green, or verified behavior>

### Required Testing

- Run `<test-command>` in `<working-directory>`
- Check that output contains `<expected-output-pattern>`
- Verify no regressions in adjacent code paths by running `<adjacent-test-command>`

### Verification Steps

Paste on the card before closing:

```bash
$ git status --porcelain
<empty output>

$ <test-command>
<actual output showing success>
```

## Template Usage

Copy this structure into your new card. Replace each section's content with what applies to your specific task. Keep it minimal — every word should serve verification or clarity.
