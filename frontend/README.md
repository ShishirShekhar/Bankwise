# Bankwise frontend

Static-export Next.js application for the Bankwise FD comparison journey. Start with the root [README](../README.md), then see [product behavior](../docs/product-specification.md), [architecture](../docs/architecture.md), [API contract](../docs/api.md), and [deployment](../docs/deployment.md).

## Local development

```sh
npm ci
cp .env.example .env.local
# Fill in Firebase web app values in .env.local
npm run dev
```

The local API origin defaults to `http://localhost:8080`. Start the backend separately. A Firebase project with Email/Password and Google sign-in enabled is needed to exercise browser authentication. Do not commit `.env.local`.

## Checks

```sh
npm run lint
npm run typecheck
npm run build
```

## Code map

- `app/`: route entry points (`/`, `/login`, `/compare`, `/dashboard`).
- `components/`: page compositions and reusable UI grouped by flow.
- `hooks/`: auth gating and comparison/session flow.
- `lib/`: API client, auth, input redaction, formatting and typed view adapters.

The frontend renders backend-calculated amounts and trade-off metrics. Do not duplicate authoritative financial calculations in browser code. Production builds a static export in `out/`; Firebase Hosting rewrites `/api/**` to Cloud Run.
