# AI Builder Cup 2026 submission readiness

Last checked: 17 October 2026. The host's submission deadline is 18 October 2026.

This page maps the supplied Ask the Expert checklist to the repository. It distinguishes implemented behavior from items that need live Google Cloud access or submission materials; a configured deployment workflow does not prove that a public deployment is reachable.

## Readiness checklist

| Requirement | Repository evidence | Status / action |
|---|---|---|
| Team eligibility | Not verifiable in source code | Each team member should confirm the host's professional-only eligibility requirement. Check the official program rules for team composition and any travel or sponsorship terms. |
| Deployed judge-accessible prototype on Cloud Run or Firebase Hosting | `.github/workflows/deploy-production.yaml`, `firebase.json`, and [deployment guide](deployment.md) | Deployment path is configured. Live reachability could not be verified from this environment; open both deployed URLs and complete a comparison before submission. |
| Meaningful Gemini use | Vertex AI Search grounding in `backend/app/ai/research.py`; optional Google ADK explanation in `backend/app/ai/orchestrator.py` | Implemented. The comparison UI now displays accepted Gemini prose separately and reports when it is unavailable. Production config enables ADK explanation. Confirm the deployed response reports `ai.status=generated` for a representative request. |
| Correct, deterministic FD calculations | `backend/app/calculators/fd.py` and `backend/tests/test_fd_calculator.py` | Implemented with unit tests; results are explicitly estimates where bank-specific day-count rules are unsupported. |
| Verified, grounded product data | `backend/data/fd-products.json`, `backend/app/domain/sources.py`, `backend/app/domain/conflicts.py` | Implemented. Open conflicts and records marked for re-verification are blocked from authoritative calculation. Refresh and review production data before judging. |
| End-to-end request flow | `/api/ask`, `backend/tests/test_decision_workflow.py`, `backend/tests/test_agent_evals.py`, and `backend/evals/bankwise_agent/` | Implemented with offline acceptance cases. Run the complete flow against the deployed services before submission. |
| Deployment, database, authentication, and APIs remain available | Production workflow provisions Cloud Run and Firebase Hosting; production uses BigQuery and Firestore | Infrastructure configuration exists. Availability and IAM/API configuration require a live smoke check and periodic checks during evaluation. |
| Pitch deck, 3–4 minute video, and project description | Not present in this repository | Prepare and submit these separately. A concise video outline is below. |
| Accessible GitHub repository | Git remote is configured for `ShishirShekhar/Bankwise` | Confirm repository visibility or grant judge access; no access assumptions should be made from the local checkout. GitHub also reported two Dependabot alerts (one high and one low) during the branch push; review them in the repository's Security tab. |
| Secrets protected | `.gitignore`, GitHub Actions Workload Identity Federation, Secret Manager release configuration | Design is configured. Review tracked files and GitHub variables/secrets before publishing; never place credentials in the repository or demo recording. |
| Sample questions and expected behavior | This page and `backend/evals/bankwise_agent/bankwise_agent.eval.json` | Added below for consistent judge testing. |

## Judge smoke test

Use the deployed public URL and a judge account or demo account configured in Firebase. The current product journey requires sign-in before `/api/ask`; there is no anonymous comparison mode.

1. Submit **“Compare FDs for ₹5 lakh over 2 years; I may need to withdraw early.”** Expect the app to parse amount, duration, and liquidity intent, show only currently eligible source-backed products, display the deterministic maturity and gains/give-ups, link sources, and state when withdrawal terms are incomplete. A Gemini explanation may appear separately when Vertex AI is available; it must not change the figures.
2. Submit **“Compare FDs for ₹2 lakh.”** Expect a request for the missing duration; the app must not guess one or calculate maturity.
3. Submit a request about a savings account, loan, or card. Expect a clear unsupported-category response rather than invented product comparisons.
4. In the evaluation fixtures, verify that an unverified or conflicting rate is blocked and that sensitive text is redacted. Do not use real personal or banking credentials in a demo.

Returned rates and amounts depend on the currently verified catalogue. Treat the examples as workflow checks, not promised financial outputs.

## Pre-submission and evaluation operations

- Confirm the Firebase Hosting URL loads without authentication errors and the Cloud Run `/api/health` endpoint responds. Then complete the judge smoke test above; a healthy endpoint alone does not prove BigQuery, Firestore, Firebase Auth, or Vertex AI access.
- Confirm Firebase providers and judge access, Cloud Run runtime IAM, BigQuery datasets, Firestore, Vertex AI APIs, Search grounding, and required GitHub Actions variables/secrets.
- Review open conflicts and source freshness through `/api/conflicts` and `/api/verification/run`; refresh any production facts that are no longer current. Do not promote research candidates without source review.
- Check GitHub Actions and deploy using the documented published-release workflow. Keep the deployed URL stable and check it during the evaluation period. Scaling to zero is supported; use a temporary minimum instance only if a known judging window justifies its cost.
- Test a representative full request and a temporary Gemini failure. The API keeps its deterministic result when optional model generation is unavailable. Search grounding has a bounded request timeout; avoid repeated retries that consume quota.
- Before sharing, inspect the repository for committed credentials and ensure build/deploy secrets are supplied through GitHub configuration and Google Secret Manager.

## Suggested 3–4 minute video

| Time | Show and explain |
|---|---|
| 0:00–0:25 | State the problem: headline FD rates hide maturity differences, source quality, and withdrawal trade-offs. Introduce people deciding where to place a fixed amount for a known duration. |
| 0:25–1:30 | Start with the real product. Enter the ₹5 lakh / 2 year / early-withdrawal example. Show parsed requirements, verified product cards, sources, maturity estimates, and the “What Am I Giving Up?” comparison. |
| 1:30–2:10 | Explain that Python code calculates all financial amounts and trade-offs from eligible, source-verified catalogue facts. Show how missing or conflicting evidence is blocked and disclosed. |
| 2:10–2:50 | Show the Gemini explanation when it is generated. Explain that Vertex AI Gemini/Google Search grounds research and Google ADK produces constrained prose over verified comparison context; deterministic calculations and metrics remain authoritative. |
| 2:50–3:30 | Show the Cloud Run API, Firebase Hosting/Auth, BigQuery catalogue and research corpus, and Firestore sessions. Mention bounded retrieval, Search fallback, and deterministic fallback when Gemini is unavailable. |
| 3:30–3:50 | Summarize practical value and limitations: estimates follow a generic formula where bank-specific day-count treatment is unavailable, and users should check linked official terms before investing. |

Keep the narration and screens readable. Show actual deployed behavior and outputs; do not present a mock response as a live result. The project description should briefly cover the FD decision problem, verified-source and deterministic-calculation approach, and the Google Cloud services used.

## Implemented reliability and cost choices

- Requirement parsing and financial calculations are deterministic, so ordinary requests do not spend a model call to interpret numbers or calculate maturity.
- BigQuery RAG retrieves a bounded number of current eligible chunks; Google Search grounding runs only when the internal evidence path has no eligible result.
- ADK explanation is one optional request-scoped call. The primary response remains usable if it times out or fails validation.
- BigQuery vector search uses exact search without a vector index at the current initial scale. Cloud Run can scale to zero.

Revisit these choices if catalogue volume, measured latency, or judging traffic changes. Firestore Vector Search versus AlloyDB AI is a workload decision; the example scale in the session notes is not a mandatory migration threshold.
