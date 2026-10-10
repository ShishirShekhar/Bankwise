This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

The UI uses system font stacks so production builds do not depend on downloading fonts.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

## BankWise routes

- `/` is the public Fixed Deposit comparison landing page. Submitted queries are redacted and held in session storage while the visitor signs in.
- `/login` uses Firebase Web SDK email/password sign-in, account creation, and Google popup sign-in. The ID token is exchanged once for a FastAPI HTTP-only session cookie, then Firebase client state is cleared.
- `/compare` shows API-returned deterministic gains and give-ups, sourced product details, and the structured explanation.
- `/dashboard` keeps Fixed Deposits available and labels Savings Accounts, Loans, and Credit Cards as coming soon.

## Frontend structure

Route files under `app/` stay thin and delegate to page compositions in `components/`. Components are grouped by flow (`landing`, `auth`, `compare`, and `dashboard`), with reusable brand, query-form, and trust components in `components/shared/`. Query execution and result-session access live in `hooks/`; API types, redaction, formatting, and trade-off selection live in `lib/`.

Run `npm run lint`, `npm run typecheck`, and `npm run build` from this directory before submitting frontend changes.

Set `NEXT_PUBLIC_BANKWISE_API_URL` to the backend origin locally (defaults to `http://localhost:8080`); leave it unset for same-origin production requests. Copy `.env.example` to `.env.local` and set the Firebase Web App values. Enable Email/Password and Google providers and configure Authorized domains in Firebase. The backend verifies ID tokens and issues the session cookie; see `../backend/README.md`.

Production hosting should route `/api/**` from Firebase Hosting to the Cloud Run backend and all other paths to the frontend. Add `firebase.json` rewrites only after the Cloud Run service name and region are known; neither is present in this repository.
