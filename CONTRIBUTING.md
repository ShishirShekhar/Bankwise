# Contributing to Bankwise

## Branches

Use:

feature/<name>
fix/<name>
refactor/<name>
docs/<name>

Example:

feature/fd-comparison
fix/fd-calculation
feature/source-verification

## Pull Requests

Every PR must:

- Have a clear description.
- Pass CI.
- Include tests for new logic.
- Update documentation when architecture changes.
- Avoid unrelated changes.

Use the checklist in [`.github/pull_request_template.md`](.github/pull_request_template.md).
For user-facing financial copy, confirm that API fields contain plain language and
that structured catalogue records are not rendered directly. Include a screenshot
or a short before/after description when the UI changes.

## Financial Logic

Changes to financial calculations require:

- Unit tests
- Example inputs/outputs
- Explanation of the calculation rule
- Source/reference for bank-specific behavior

## AI Changes

Changes to:

- Prompts
- Agents
- Tools
- RAG
- Model configuration

must include relevant evaluation cases.

## Commits

Use:

feat:
fix:
refactor:
docs:
test:
chore:

Examples:

feat: add FD comparison engine
fix: correct quarterly FD calculation
docs: document source verification
test: add FD maturity cases
