# Bankwise — AI Development Rules

## Project

Bankwise is an AI-powered financial-product comparison and decision-support
platform.

The initial MVP focuses on Fixed Deposits (FDs).

## Core Principle

Bankwise must provide source-grounded financial information and deterministic
financial calculations.

The AI must never invent financial facts.

## Mandatory Rules

### 1. Financial calculations

Never use an LLM to perform authoritative financial calculations.

All calculations must be implemented in deterministic, tested code.

Examples:

- FD maturity
- Interest earned
- EMI
- Loan total cost
- Credit-card cost
- Penalties

### 2. Financial data

Never invent:

- Interest rates
- Fees
- Penalties
- Eligibility rules
- Tenure
- Minimum balance
- Product conditions
- Effective dates

Every important financial fact must have source metadata (`url`, `retrieved_at`, `verified_at`, `confidence`).

### 3. Core Differentiator: "What Am I Giving Up?"

Do not simply compare headline rates or declare a single "best" bank.

The core differentiator is explaining the actual trade-offs:
- For every product option, determine concrete **gains** (e.g., higher maturity by ₹X, lower penalty) and **give-ups** (e.g., ₹X lower maturity compared to top earner, less flexible early withdrawal).
- Always surface this trade-off matrix in the API response and UI.
- Never let Gemini replace or overwrite these deterministic trade-off metrics.

### 4. Sources

Prefer:

1. Official bank sources
2. Official bank PDFs/rate cards
3. RBI/government sources
4. Trusted secondary sources

Search snippets must not be treated as authoritative financial data.

### 5. Conflicting data

If two relevant sources disagree:

- Do not silently choose one.
- Mark the field as `CONFLICT`.
- Store both sources.
- Prevent the disputed value from being used as authoritative.
- Surface the conflict to the user/admin.

### 6. AI & Explanation Quality

Gemini may:

- Understand user intent
- Extract requirements
- Select tools
- Retrieve information
- Explain results
- Explain trade-offs

Gemini must not:

- Invent financial facts
- Replace deterministic calculations
- Hide source conflicts
- Present unsupported recommendations as facts

#### AI Explanation Layout
Whenever Gemini generates a decision explanation, it must follow a structured 3-part layout:
1. **Executive Decision Summary**: Tailored to the user's specific amount, duration, and liquidity preference.
2. **The Key Trade-off ("What Am I Giving Up?")**: Explicit comparison between top alternatives showing what is gained vs sacrificed.
3. **Critical Conditions & Transparency**: Notes on compounding frequency, penalty clauses, and source verification dates.

### 7. Privacy

Never request, log, or store:

- PAN
- Aadhaar
- Bank account numbers
- Card numbers
- CVV
- UPI credentials
- Banking passwords

All natural language user input must be sanitized via `redact_sensitive_input()`.

### 8. Environment & Architecture

To enable frictionless local development while strictly enforcing Google Cloud services in production, services must respect `ENVIRONMENT`:

- `ENVIRONMENT=development` (Default local):
  - Catalog: `LocalJsonCatalog` (reads `backend/data/fd-products.json`).
  - Sessions: `MemorySessionRepository`.
  - Works fully offline anywhere without GCP credentials.
- `ENVIRONMENT=production` (Google Cloud / Cloud Run):
  - Catalog: `BigQueryRepository` (`bankwise` dataset in BigQuery).
  - Sessions: `FirestoreSessionRepository`.
  - Gemini on Vertex AI + Google ADK.

Prefer Google Cloud services for deployment:
- Gemini / Vertex AI
- Google ADK
- Cloud Run
- Cloud SQL / BigQuery
- Firestore
- Cloud Storage
- Vertex AI Agent Search
- Secret Manager
- Cloud Build

### 9. Code Quality & Modularity

Before creating or modifying code:

1. Keep business logic strictly separate from AI logic.
2. Keep financial calculations independent from Gemini.
3. Keep source verification independent from UI.
4. **No dead or commented-out code**: Do not leave commented alternative implementations or imports in production files. Use modular dependency injection via `ENVIRONMENT`.
5. Maintain strict typing (Pydantic models in Python, strong TypeScript types in frontend, no `any`).
6. Remove unused legacy layers and keep code clean and easy to understand.

### 10. Frontend User Journey

- **`/` (Public Landing Page)**:
  - Hero and primary natural-language query input box.
  - Explanatory value propositions and trust badges.
  - If an unauthenticated user submits a query, save the query in session state and redirect to `/login?redirect=/compare`.
  - If authenticated, execute the query and navigate directly to `/compare`.
- **`/login` (Authentication)**:
  - Sign-in page with email/password and a one-click demo login option.
  - Automatically redirects back to comparison results after authentication.
- **`/compare` (Results)**:
  - Top 2 Bank Trade-off Banner ("What Am I Giving Up?").
  - Verified product cards with gains and give-ups.
  - Gemini 3-part structured explanation.
  - Excluded products list with transparent reasons.
- **`/dashboard`**:
  - Focus 100% on Fixed Deposits; non-FD categories (Savings, Loans, Cards) are clearly marked with "Coming Soon" badges for the MVP.

### 11. Testing

Every financial calculation requires unit tests (`backend/tests/test_fd_calculator.py`).

Every source-verification rule and conflict detection rule requires tests.

Every important agent workflow requires evaluation cases.

CI must pass with 100% test coverage for calculations and source rules.

## Definition of Done

A feature is complete only when:

- Implementation exists and is modular.
- Dead or commented-out code is removed.
- Tests exist and pass (`pytest` / `npm run typecheck` / `npm run lint`).
- Documentation is updated.
- Source attribution exists where applicable.
- Security/privacy requirements are satisfied.
- CI passes.
