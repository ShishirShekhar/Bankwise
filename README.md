# Bankwise

> Source-grounded financial-product comparison and decision support.

## Problem

Finding financial-product information is easy.

Understanding the actual financial outcome, conditions, penalties,
fees, liquidity and trade-offs is difficult.

## Solution

Bankwise parses FD requirements, compares source-verified products, performs
deterministic calculations, and explains trade-offs from verified result data.
The current decision response does not use model-generated financial prose.

## Example

> I have ₹5 lakh and want to invest for 2 years.
> I may need the money early.

Bankwise:

1. Understands the requirement.
2. Finds relevant products.
3. Verifies banking data.
4. Calculates expected outcomes.
5. Compares conditions and liquidity.
6. Explains the trade-offs.
7. Shows the sources.

## Current MVP

The MVP focuses on Fixed Deposits.

Supported:

- Product comparison
- FD calculations
- Liquidity comparison
- Premature withdrawal comparison
- Source verification
- Conflict detection
- Structured, deterministic explanations

## Architecture

```text
User
 ↓
Next.js
 ↓
Cloud Run / FastAPI
 ↓
Requirement parsing and decision API
 ↓
Research / Calculation / Verification
 ↓
BigQuery catalogue + Firestore sessions
 ↓
Decision Engine
 ↓
Deterministic Explanation
```

## Backend

The Python FastAPI service is in [`backend/README.md`](backend/README.md). It reads curated product and source records from BigQuery and stores redacted decision-session state in Firestore. The catalogue starts empty until official product data and source metadata are curated.

## Continuous integration

GitHub Actions runs `frontend-lint`, `frontend-typecheck`, `frontend-build`,
`backend-lint`, and `backend-test` for pull requests and pushes to `main`. To make these checks
block merges, configure the repository's branch protection or ruleset for
`main` and require all five status checks.
