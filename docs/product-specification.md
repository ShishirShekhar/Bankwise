# Product specification

## Purpose

Bankwise helps a person compare fixed deposits using their investment amount, intended duration, and stated need for liquidity. The central question is **“What am I giving up?”** A user should see the return difference and verified early-withdrawal conditions, not only a headline rate or unsupported “best bank” claim.

## Users and journey

The public landing page accepts a natural-language query. An unauthenticated visitor's redacted query is held in browser session state and the visitor is sent to sign in. After Firebase sign-in, the app exchanges the ID token for a short-lived HTTP-only backend session, then returns to the comparison route. The comparison screen shows eligible sourced options, calculations, trade-offs, conditions and excluded products. Dashboard categories other than FDs are marked as coming soon.

## Supported behavior

- Parse rupee amount and duration stated in years or months.
- Ask the user to supply a missing amount or duration; do not guess either.
- Compare active FD products with one eligible rate band for the amount and duration.
- Calculate maturity only from an authoritative rate with a supported cumulative payout and compounding frequency.
- Show source metadata, conditions, warnings, excluded options and deterministic gains/give-ups.
- Identify unsupported categories such as loans, savings accounts and credit cards rather than pretending to compare them.

## Out of scope today

Automated bank-site crawling, automatic source refresh, write/admin UI for catalog curation, non-FD product comparisons, early-exit amount estimates, and bank-specific day-count calculation are not implemented. Early withdrawal conditions may be shown when verified, but a withdrawal amount cannot be calculated without a withdrawal date and a supported bank-specific rule.

## Product principles

1. Never invent rates, terms, or source dates.
2. Never let a language model perform or overwrite financial calculations or trade-off metrics.
3. Surface both sides of the decision, including uncertainty and exclusions.
4. Do not retain raw natural-language input in backend decision sessions; redact it before processing.
5. Treat missing, stale, or disputed facts as unusable for authoritative calculations.

## Completion expectations

User-visible financial facts must link to provenance; calculation and source rules need automated tests; and docs must describe shipped behavior. See the project [definition of done](../AGENTS.md).
