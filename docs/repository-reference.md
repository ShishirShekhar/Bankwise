# Repository reference

This is the directory-by-directory lookup guide to the tracked project. “Source” means code/configuration used to build or run the application; dependency internals, local secrets, caches and generated output are not part of this list. For an explanation of how the parts work together, read the [codebase walkthrough](codebase-walkthrough.md).

## Root files

| File | Purpose |
|---|---|
| `README.md` | Project introduction, quick start, checks, and documentation index. |
| `AGENTS.md` | Project-specific development and product rules, including financial safety and privacy requirements. |
| `AGENT_GUIDE.md` | Guidance for AI coding agents working in the repository. |
| `CONTRIBUTING.md` | Contribution workflow and expectations. |
| `SECURITY.md` | Security reporting and project security guidance. |
| `LICENSE` | Repository license terms. |
| `.gitignore` | Root-level files excluded from Git. |
| `firebase.json` | Firebase Hosting output directory, API rewrite, and response headers. |

## `.github/`

| File | Purpose |
|---|---|
| `ISSUE_TEMPLATE/ai---agent-change.md` | Intake template for AI/agent behavior changes. |
| `ISSUE_TEMPLATE/bug-report.md` | Bug report template. |
| `ISSUE_TEMPLATE/feature-request.md` | Feature proposal template. |
| `ISSUE_TEMPLATE/financial-data---calculation.md` | Intake template for financial facts or calculation changes. |
| `ISSUE_TEMPLATE/task---engineering-work.md` | General engineering task template. |
| `actions/derive-service-accounts/action.yaml` | Reusable GitHub Action deriving deployment/runtime service account identities. |
| `actions/get-env-values/action.yaml` | Reusable action loading values from the production configuration. |
| `config/production.yaml` | Non-secret Google Cloud, Firebase, and Cloud Run production settings. |
| `dependabot.yml` | Automated dependency update configuration. |
| `pull_request_template.md` | Pull request checklist and description structure. |
| `workflows/backend.yaml` | Backend lint and test CI workflow. |
| `workflows/frontend.yaml` | Frontend lint, typecheck, and build CI workflow. |
| `workflows/deploy-production.yaml` | Release-triggered Cloud Run and Firebase Hosting deployment. |

## `docs/`

| File | Purpose |
|---|---|
| `codebase-walkthrough.md` | Beginner-oriented setup and end-to-end code flow. |
| `repository-reference.md` | This file map. |
| `product-specification.md` | Product goals, journey, supported scope, and principles. |
| `architecture.md` | Main components, dependency selection, request flow, and security boundary. |
| `data-model.md` | Catalogue entities and provenance relationships. |
| `api.md` | HTTP routes, auth requirements, request behavior, and response overview. |
| `ai-agent-architecture.md` | Live deterministic path and optional Gemini/ADK components. |
| `financial-calculations.md` | FD formula, requirements, rounding, and limitations. |
| `verification-system.md` | Freshness, confidence, conflict handling, and verification endpoint. |
| `deployment.md` | Local setup, cloud setup, release process, and troubleshooting. |

## `backend/`

### Backend project files

| File | Purpose |
|---|---|
| `README.md` | Backend quick reference and links into the project docs. |
| `.env.example` | Safe local/cloud configuration template; copy to `.env` locally. |
| `.gitignore` | Backend-local ignore rules. |
| `requirements.txt` | Runtime Python package dependencies. |
| `requirements-dev.txt` | Development dependencies layered on runtime packages. |
| `Dockerfile` | Container image definition; defaults to production environment on Cloud Run. |
| `data/fd-products.json` | Local catalogue and source observations used in offline mode. |
| `sql/bigquery_schema.sql` | Production BigQuery tables for banks, products, rates, conditions, sources, verification, and conflicts. |
| `scripts/create_bigquery_dataset.py` | Creates configured BigQuery dataset/tables from the SQL schema. |
| `scripts/import_fd_products.py` | Previews or upserts local catalogue records to BigQuery. |

### `backend/app/` application code

| File | Purpose |
|---|---|
| `__init__.py` | Marks the app directory as a Python package. |
| `main.py` | Creates the FastAPI app, middleware, error handling, CORS, and route registration. |
| `config.py` | Loads environment settings and validates production requirements. |
| `schemas.py` | Pydantic models for API request and response fields. |
| `firebase.py` | Firebase Admin initialization, ID token/session cookie verification. |
| `logging_config.py` | Structured log formatting and request ID context. |
| `tools.py` | Deterministic calculation and verification functions exposed to optional agents. |

### `backend/app/api/` routes and HTTP security

| File | Purpose |
|---|---|
| `__init__.py` | Marks API routes as a package. |
| `assistant.py` | Authenticated natural-language comparison endpoint, `POST /api/ask`. |
| `auth.py` | CSRF token, Firebase session creation, current-user and logout routes. |
| `catalog.py` | Product listing/details, calculation, and comparison endpoints. |
| `dependencies.py` | Selects repository implementations for local or production. |
| `operations.py` | Health, stored-data verification, conflict list, and agent configuration status. |
| `security.py` | Session cookie settings, CSRF signing/checks, and per-user ask limit. |
| `sessions.py` | Retrieves a saved decision session only for its owner. |

### `backend/app/domain/` business rules

| File | Purpose |
|---|---|
| `__init__.py` | Marks domain rules as a package. |
| `catalog.py` | Shapes product, source, condition, and conflict records for API responses. |
| `comparison.py` | Compares eligible results and creates deterministic gains/give-ups. |
| `conflicts.py` | Detects disagreements among sourced observations and handles explicit resolutions. |
| `identifiers.py` | Generates IDs for decision requests and sessions. |
| `input.py` | Redacts sensitive content and extracts stated requirements; includes an optional Gemini branch. |
| `models.py` | Typed Pydantic bank/product models matching catalogue rows. |
| `rates.py` | Selects eligible rate bands, verifies usability, and calls the FD calculator. |
| `sources.py` | Evaluates source authority, age, effective dates, and fact status. |

### `backend/app/calculators/`

| File | Purpose |
|---|---|
| `__init__.py` | Marks calculator modules as a package. |
| `fd.py` | Deterministic Decimal compound-interest calculation and validation. |

### `backend/app/repositories/`

| File | Purpose |
|---|---|
| `__init__.py` | Marks repository adapters as a package. |
| `local_json.py` | Reads and normalizes the local JSON catalogue. |
| `bigquery.py` | Reads production catalogue and verification records from BigQuery. |
| `memory_sessions.py` | Stores temporary local decision sessions in process memory. |
| `firestore.py` | Persists decision sessions to Firestore in production. |

### `backend/app/ai/` and evaluations

| File | Purpose |
|---|---|
| `ai/ask_response.py` | Converts internal deterministic decision data into the frontend response format. Despite the directory name, this response shaping is ordinary Python, not model generation. |
| `ai/decision_workflow.py` | Redacts/parses a query, compares, persists, and builds the live decision context; currently does not invoke Gemini. |
| `ai/orchestrator.py` | Defines optional ADK agents for grounded explanation/calculation integrations. |
| `evals/__init__.py` | Evaluation package marker. |
| `evals/fd_calculation/__init__.py` | FD calculation evaluation package marker. |
| `evals/fd_calculation/agent.py` | Optional ADK evaluation agent definition. |
| `evals/fd_calculation/fd_calculation.test.json` | Evaluation cases for expected calculator tool behavior. |
| `evals/fd_calculation/test_config.json` | ADK evaluation configuration. |

### `backend/tests/`

| File | Behavior covered |
|---|---|
| `conftest.py` | Shared API test client, auth override, and fixtures. |
| `test_ask_response.py` | Internal decision result to API response mapping. |
| `test_auth.py` | Session bootstrap, authentication, CSRF, and protected route behavior. |
| `test_comparison_tradeoffs.py` | Gains, give-ups, and top-option summary. |
| `test_conflicts.py` | Conflict creation, resolution, API visibility, and blocked facts. |
| `test_decision_workflow.py` | Query redaction, requirement handling, comparison call, and persistence. |
| `test_environment_config.py` | Local/production config and repository selection requirements. |
| `test_fd_calculation_tool.py` | Tool result consistency and evaluation fixture behavior. |
| `test_fd_calculator.py` | Formula, rounding, invalid inputs, and calculation warning. |
| `test_import_fd_products.py` | Catalogue import mapping and safety checks. |
| `test_input_redaction.py` | Sensitive input redaction and explicit requirement extraction. |
| `test_local_catalog.py` | Local JSON catalogue shape and product comparisons. |
| `test_logging_config.py` | Request logging and exclusion of sensitive data. |
| `test_session_ownership.py` | Session persistence and owner-only retrieval. |
| `test_source_rules.py` | Source freshness, authority, conflict effects, and calculation eligibility. |

## `frontend/`

### Frontend project and configuration

| File | Purpose |
|---|---|
| `README.md` | Frontend run/check commands and structure overview. |
| `.env.example` | Firebase web settings and local API origin template. |
| `.gitignore` | Frontend-local ignore rules. |
| `.prettierignore` | Files excluded from formatting checks. |
| `.prettierrc` | Prettier formatting preferences. |
| `AGENTS.md` | Frontend-specific development instructions, including framework guidance. |
| `CLAUDE.md` | Additional frontend coding-agent instructions. |
| `package.json` | Package metadata, npm scripts, and dependency declarations. |
| `package-lock.json` | Exact resolved npm dependency tree used by `npm ci`. |
| `tsconfig.json` | TypeScript compiler settings and import aliases. |
| `next.config.ts` | Next.js static export, typed routes, and image settings. |
| `postcss.config.mjs` | CSS processing and Tailwind plugin setup. |
| `eslint.config.mjs` | Frontend lint rules. |

### `frontend/app/` routes and global shell

| File | Purpose |
|---|---|
| `layout.tsx` | Shared document metadata, styles, auth provider, and error reporter. |
| `globals.css` | Global Tailwind/CSS styles. |
| `page.tsx` | `/` route, delegates to landing page component. |
| `login/page.tsx` | `/login` route, loads sign-in page component. |
| `compare/page.tsx` | `/compare` route, loads comparison page component. |
| `dashboard/page.tsx` | `/dashboard` route, loads dashboard component. |
| `product/page.tsx` | `/product` route, loads selected product detail view. |
| `favicon.ico` | Browser tab icon. |

### `frontend/components/`

| File | Purpose |
|---|---|
| `auth/AuthProvider.tsx` | Shares backend-authenticated user/session state with client components. |
| `auth/LoginBrandPanel.tsx` | Branding panel in the login view. |
| `auth/LoginForm.tsx` | Email/password login and account creation form. |
| `auth/LoginPage.tsx` | Coordinates sign-in, pending query continuation, and redirect. |
| `compare/ComparisonOverview.tsx` | Displays the request and result overview. |
| `compare/ComparisonPage.tsx` | Auth gate and composition of comparison result sections. |
| `compare/ComparisonWarnings.tsx` | Displays calculation/source warning messages. |
| `compare/DecisionAnswer.tsx` | Displays the primary decision summary. |
| `compare/ExplanationContent.tsx` | Renders the explanation text safely as structured content. |
| `compare/NoComparison.tsx` | Empty state when no comparison is available. |
| `compare/ProductCard.tsx` | One FD option card. |
| `compare/ProductResults.tsx` | List of eligible result cards. |
| `compare/SkippedProducts.tsx` | Products omitted from calculated options and the reasons. |
| `compare/SourceLink.tsx` | Link to a product source. |
| `compare/StructuredExplanation.tsx` | Displays the three-part explanation. |
| `compare/TradeoffBanner.tsx` | Top-option comparison banner. |
| `compare/TradeoffPoints.tsx` | Lists per-option gains and give-ups. |
| `dashboard/DashboardHeader.tsx` | Dashboard heading and navigation. |
| `dashboard/DashboardIntro.tsx` | Dashboard intro copy. |
| `dashboard/DashboardPage.tsx` | Dashboard composition and FD query form. |
| `dashboard/ProductCategories.tsx` | FD availability and coming-soon categories. |
| `dashboard/WhyBankwise.tsx` | Product value/trust explanation. |
| `landing/LandingHero.tsx` | Landing-page headline and intro. |
| `landing/LandingPage.tsx` | Public landing page composition and query submission. |
| `shared/BankwiseQueryForm.tsx` | Reusable natural-language query form. |
| `shared/BrandMark.tsx` | Reusable Bankwise brand mark. |
| `shared/ClientErrorReporter.tsx` | Browser-side integration for sanitized client error reporting. |
| `shared/SiteHeader.tsx` | Shared site header/navigation. |
| `shared/TrustHighlights.tsx` | Landing-page trust/value highlights. |

### `frontend/hooks/` and `frontend/lib/`

| File | Purpose |
|---|---|
| `hooks/use-bankwise-query.ts` | Redacts, checks auth, submits query, saves latest result, and navigates. |
| `hooks/use-last-ask.ts` | Reads/parses the latest ask result from session storage. |
| `hooks/use-require-auth.ts` | Redirects protected pages to login when there is no session. |
| `lib/api-client.ts` | Fetch wrapper with credentials, CSRF token, safe errors, and request ID handling. |
| `lib/auth.ts` | Firebase sign-in and backend session API calls. |
| `lib/bankwise.ts` | Typed API response shapes, query redaction, formatting, and ask request. |
| `lib/decision-explanation.ts` | Frontend explanation parsing/formatting helpers. |
| `lib/error-reporting.ts` | Safe client error category reporting. |
| `lib/firebase.ts` | Firebase Web SDK app/auth initialization. |
| `lib/session-storage.ts` | Browser tab session-storage hooks and update notifications. |
| `lib/tradeoff-view.ts` | Chooses options for the top trade-off banner. |

### `frontend/public/`

| File | Purpose |
|---|---|
| `file.svg` | Default static icon asset. |
| `globe.svg` | Default static icon asset. |
| `next.svg` | Next.js static logo asset. |
| `vercel.svg` | Default static logo asset. |
| `window.svg` | Default static icon asset. |

## Finding the right tests

Start with the tests named in the corresponding backend section above. For frontend edits, use the scripts in `frontend/package.json`: `npm run lint`, `npm run typecheck`, and `npm run build`. CI definitions in `.github/workflows/` show which checks run for changes and releases. The project expects financial and verification rule changes to come with tests; see root `AGENTS.md`.
