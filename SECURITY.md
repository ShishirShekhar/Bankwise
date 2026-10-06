# Security Policy

## Sensitive Data

Bankwise must never request or store:

- PAN
- Aadhaar
- Bank account numbers
- Debit/credit card numbers
- CVV
- UPI credentials
- Banking passwords

## Secrets

Never commit:

- API keys
- Service-account keys
- Database passwords
- OAuth secrets
- `.env` files

Use Google Secret Manager for production secrets.

## Reporting

Security issues should be reported privately to the project maintainers
rather than through public GitHub issues.

## Security and privacy review (2026-10-07)

Checked against issue #48.

| Area | Result |
|---|---|
| Secrets in repository and git history | None found (API keys, private keys, tokens, service-account JSON). `.env` files are git-ignored; only `backend/.env.example` with empty values is tracked. |
| Sensitive user input | Free text is redacted before Gemini, ADK, or storage (`backend/app/domain/input.py`). Fixed gaps: 3-digit CVV, passwords (including "netbanking password"), OTP, MPIN, PIN, UPI IDs, email addresses, labelled account numbers (`account no`, `a/c`, `acct`), spaced Aadhaar numbers (8 of 12 digits previously leaked), and 13-19 digit card numbers. Covered by `tests/test_input_redaction.py`, including a linear-time check. |
| Storage | Sessions store parsed requirements and comparison results only, never the raw query. Session IDs are random UUID4 values. |
| Logs | The backend has no application logging of request bodies or queries. |
| Dependencies | `google-adk` raised to `>=1.28.1` (PYSEC-2026-344). Production npm dependencies: no known vulnerabilities. |
| Container | The backend image now runs as a non-root user. |
| CI | Workflows use read-only `contents` permission and no secrets. |
| Web | CORS origins come from `CORS_ORIGINS`, credentials disabled, GET/POST only. Request size limits on free text (4000 chars) and product lists (20). Frontend sends `nosniff`, `Referrer-Policy`, `Permissions-Policy`, and HSTS headers. |

Open items:

- `starlette` 0.52.x has advisories (PYSEC-2026-161, -248, -249, -2280, -2281) fixed only in 1.x, which `google-adk` 1.x does not allow. Bankwise does not use the affected features (`StaticFiles`, `HTTPEndpoint`, form parsing, `request.url`). Fixing requires moving to `google-adk` 2.x.
- Five high-severity npm advisories are in development-only tooling (`eslint-config-next`), not in the shipped app.
- The API has no authentication; it serves public catalogue data, and `/api/sessions/{id}` relies on unguessable IDs. Revisit if user accounts are added.
- Service accounts, Secret Manager, least-privilege IAM, and Cloud Logging/trace settings (ensure prompts are not exported) must be checked when deploying (#41, #43).
- Labelled 9-11 digit account numbers are redacted, but unlabelled ones are not, to avoid removing deposit amounts.
