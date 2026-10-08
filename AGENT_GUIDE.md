# Bankwise — Agent & Architecture Guide

> **Single Source of Truth for all AI Agents and Developers working on Bankwise.**
> This guide preserves the core decisions aligned during the design interview and must be strictly followed in all sessions.

---

## 1. System Philosophy & Non-Negotiables

Bankwise is an AI-powered financial decision engine designed to turn fragmented banking product information into explainable, personalized financial decisions.

### Core Principles
1. **Never Invent Financial Facts**: Never guess, estimate in free text, or hallucinate interest rates, fees, penalties, tenures, eligibility, or dates.
2. **Deterministic Calculations Only**: Authoritative monetary calculations (FD maturity, interest earned, penalties) must **always** be performed by tested Python functions (`app/calculators/fd.py`), never by LLM arithmetic.
3. **Core Differentiator — Trade-offs ("What Am I Giving Up?")**:
   Do not merely rank products or state "Bank A has the highest rate". Always explain the concrete financial trade-offs: what a user gains vs what they sacrifice when choosing one bank over another.
4. **Source Attribution & Conflict Transparency**:
   Every financial fact must have source provenance (`url`, `retrieved_at`, `verified_at`, `confidence`). If sources conflict, mark as `CONFLICT` and never use the disputed value silently.
5. **Absolute User Privacy**:
   Never collect, ask for, or store PAN, Aadhaar, account numbers, debit/credit card numbers, CVVs, UPI PINs, or banking passwords. Always pass user input through `redact_sensitive_input()`.

---

## 2. Environment Architecture & Data Switching

To enable seamless local development and testing from anywhere while strictly enforcing Google Cloud (BigQuery, Firestore) in production, all services respect the `ENVIRONMENT` configuration:

| Setting | `ENVIRONMENT=development` (Default locally) | `ENVIRONMENT=production` (Cloud Run / GCP) |
|---|---|---|
| **Product Catalogue** | `LocalJsonCatalog` (reads `backend/data/fd-products.json`) | `BigQueryRepository` (`bankwise` dataset in BigQuery) |
| **Session Persistence**| `MemorySessionRepository` (in-memory) | `FirestoreSessionRepository` (Firestore collection) |
| **GCP Prerequisite** | **None** (zero friction, works completely offline) | Requires `GOOGLE_CLOUD_PROJECT`, ADC credentials |
| **Gemini / ADK** | Uses Vertex AI if project configured; else deterministic structured fallback | Full Vertex AI Gemini + Google ADK agent |

### Implementation Rules
- In `backend/app/api/dependencies.py`, inspect `ENVIRONMENT` (or `APP_ENV`).
- In `development`, return `LocalJsonCatalog()` and `MemorySessionRepository()`.
- In `production`, return `BigQueryRepository()` and `FirestoreSessionRepository()`.
- **Never leave commented-out repository code or temporary commented hacks in production route files.**

---

## 3. Backend API Contract

### Primary Decision Route: `POST /api/ask`
This is the primary user-facing contract used by the frontend:
- **Input**: `{"query": "I have ₹5 lakh and want to invest for 2 years, but may need the money early."}`
- **Processing**:
  1. Input redaction via `redact_sensitive_input(query)`
  2. Requirement extraction via `extract_requirements(query)`
  3. Product search & filtering via catalog
  4. Deterministic FD calculation via `app/calculators/fd.py`
  5. Trade-off computation (`gains` and `give_ups` per bank)
  6. Gemini ADK explanation generation
  7. Persist redacted session in repository
- **Response Format (`AskResponse`)**:
  - `status`: `"OK"` | `"NEEDS_CLARIFICATION"` | `"UNSUPPORTED"` | `"NO_MATCH"`
  - `requirements`: `{ "category": "FD", "amount": 500000, "duration_months": 24, "liquidity_need": "HIGH", "missing": [] }`
  - `options`: Array of verified FD options sorted by maturity amount. Each option contains:
    - Bank details, product name, rate, maturity, interest, early exit note
    - Sourced URLs for calculation & penalties
    - Structured `tradeoff`: `{ "gains": [...], "give_ups": [...] }`
  - `tradeoff_summary`: Overarching comparison summary between top alternatives (e.g. highest yield vs highest liquidity).
  - `explanation`: Gemini 3-part structured text (or deterministic fallback when Gemini is offline).
  - `skipped`: Array of excluded products with clear reasons.
  - `warnings` & `sources`: Provenance metadata.

### Secondary / Operational Routes
- `GET /api/products`: Filterable product catalogue
- `GET /api/products/{id}` & `/api/products/{id}/sources`: Sourced product details
- `POST /api/calculations/fd`: Direct deterministic calculation endpoint
- `POST /api/compare`: Direct multi-product comparison endpoint
- `GET /api/conflicts`: View detected source discrepancies
- `GET /api/health`: Health status and configuration check

---

## 4. AI Explanation & Output Quality Standards

### Structured 3-Part Gemini Explanation Layout
When Gemini generates an explanation (via Google ADK orchestrator in `app/ai/orchestrator.py`), it must follow this exact 3-part structure:
1. **Executive Decision Summary**:
   A concise summary answering the user's specific financial intent (e.g., investing ₹5 lakh for 24 months with high liquidity priority).
2. **The Key Trade-off ("What Am I Giving Up?")**:
   Explicit comparison of top options showing the clear gain vs sacrifice (e.g. State Bank of India provides ₹X more at maturity, but Bank of Baroda provides higher liquidity with zero premature exit penalty).
3. **Important Conditions & Source Transparency**:
   Notes on quarterly compounding convention, penalty rules, and official verification dates.

### Deterministic Trade-off Matrix
In addition to the AI prose, `app/domain/comparison.py` and `app/ai/ask_response.py` must compute deterministic `gains` and `give_ups` for every option:
- Top maturity option gains: `+ ₹X higher calculated maturity vs [next best bank]`
- Lower maturity option gains: `Lower penalty (X% vs Y%)` or `Flexible withdrawal without lock-in`
- Lower maturity option give-up: `- ₹X lower calculated maturity compared to [top bank]`

---

## 5. Frontend Architecture & User Journey

### Routing & Authentication Model
- **`/` (Landing Page — Public)**:
  - Hero: *"Make your money decisions with confidence."*
  - Big natural language query input with example prompt pills.
  - Value propositions: Sourced facts, deterministic math, trade-off intelligence.
  - **Auth Interception**:
    - If user enters a query while logged out, save the query in session storage and navigate to `/login?redirect=/compare`.
    - If user is logged in, immediately query the API and navigate to `/compare`.
- **`/login` (Auth Page)**:
  - Clean authentication interface (email/password + one-click *"Continue as Demo User"* for hackathon judging).
  - Automatically redirects back to the intended page (e.g. `/compare`) with the user's query active.
- **`/compare` (Results Page — Protected)**:
  - Requirement summary badge (e.g. ₹5,00,000 · 24 months · High liquidity).
  - Top 2 Bank Trade-off Banner: Highlight the signature *"What am I giving up?"* comparison between Option A and Option B.
  - Product Cards: Rate, estimated maturity, early withdrawal terms, Gains/Give-ups badges, and direct source links.
  - Bankwise AI Explanation: 3-part structured Gemini insight.
  - Excluded Products section: Transparency on why certain banks were excluded (e.g., tenure mismatch, open conflict).
- **`/dashboard` (Dashboard — Protected)**:
  - Quick query input.
  - Fixed Deposits tile (active).
  - Savings Accounts, Loans, Credit Cards tiles clearly marked with **"Coming Soon"** badges to keep focus 100% on the FD MVP.
- **`/product` (Product Detail — Protected)**:
  - Deep-dive into specific bank rates, compounding frequency, withdrawal policy, source documents, and verification history.

---

## 6. Codebase Quality & Cleanliness Guidelines

1. **Delete Dead & Commented-out Code**: Do not leave commented alternative implementations in production files. Use modular dependency injection via `ENVIRONMENT`.
2. **Strict Typing**:
   - Python: Pydantic v2 schemas and type annotations throughout.
   - TypeScript: Strong types in `frontend/lib/bankwise.ts`, no `any` types.
3. **Test Integrity**:
   - Every financial formula must have unit tests in `backend/tests/test_fd_calculator.py`.
   - Every source verification and conflict detection rule must have unit tests.
   - Run tests before finishing: `PYTHONPATH=. .venv/bin/pytest` must pass 100%.
   - Frontend must pass typecheck and lint: `npm run typecheck` and `npm run lint`.

