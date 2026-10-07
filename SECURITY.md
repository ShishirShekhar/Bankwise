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
