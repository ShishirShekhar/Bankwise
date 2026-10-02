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

Every important financial fact must have source metadata.

### 3. Sources

Prefer:

1. Official bank sources
2. Official bank PDFs/rate cards
3. RBI/government sources
4. Trusted secondary sources

Search snippets must not be treated as authoritative financial data.

### 4. Conflicting data

If two relevant sources disagree:

- Do not silently choose one.
- Mark the field as `CONFLICT`.
- Store both sources.
- Prevent the disputed value from being used as authoritative.
- Surface the conflict to the user/admin.

### 5. AI

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

### 6. Privacy

Never request or store:

- PAN
- Aadhaar
- Bank account numbers
- Card numbers
- CVV
- UPI credentials
- Banking passwords

### 7. Architecture

Prefer Google Cloud services:

- Gemini / Vertex AI
- Google ADK
- Cloud Run
- Cloud SQL
- Cloud Storage
- Vertex AI Agent Search
- BigQuery
- Cloud Scheduler
- Cloud Run Jobs
- Secret Manager
- Cloud Build
- Artifact Registry

### 8. Code quality

Before creating new functionality:

1. Check existing architecture.
2. Reuse existing services/tools.
3. Add tests.
4. Keep business logic separate from AI logic.
5. Keep financial calculations independent from Gemini.
6. Keep source verification independent from UI.

### 9. Changes

Do not make unrelated changes.

Do not introduce a new framework/library when an existing project dependency already solves the problem.

### 10. Testing

Every financial calculation requires unit tests.

Every source-verification rule requires tests.

Every important agent workflow requires evaluation cases.

## Definition of Done

A feature is complete only when:

- Implementation exists.
- Tests exist.
- Documentation is updated.
- Source attribution exists where applicable.
- Security/privacy requirements are satisfied.
- CI passes.
