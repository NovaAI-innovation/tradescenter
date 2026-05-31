# TradesCenter V1.5 Rollout Notes

## Backend schema
Apply base schema first (if needed):
- `tradescenter-backend/supabase/schema.sql`

Then apply the versioned migration for v1.5 additions:
- `tradescenter-backend/supabase/migrations/20260423_01_platform_v15_identity_billing_verification.sql`

This migration adds:
- identity/account tables (`accounts`, `profile_pages`, `client_profiles`, `contractor_company_profiles`)
- verification tables (`identity_verifications`, `verification_requirements`)
- billing tables (`billing_customers`, `subscriptions`, `subscription_events`, `invoices`)
- indexed discovery table (`indexed_users`)
- additive profile columns (`kyc_status`, `registration_status`, etc.)

## Required environment variables
Backend (`tradescenter-backend/.env`):
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_IDENTITY_WEBHOOK_SECRET` (optional if using one webhook secret)
- `STRIPE_PRICE_PRO`
- `STRIPE_PRICE_PLATINUM`

Frontend (`tradescenter-frontend/.env`):
- `VITE_API_BASE_URL`

## New API surface
- `GET /api/billing/subscription-status`
- `POST /api/billing/checkout-session`
- `POST /api/billing/customer-portal`
- `POST /api/billing/webhooks`
- `GET /api/verification/status`
- `POST /api/verification/identity/session`
- `POST /api/verification/webhooks`
- `GET /api/indexed-users`

## Behavior changes
- Contractor posting now requires `kyc_status = verified`.
- Contractor Studio now uses Stripe checkout/portal endpoints instead of demo tier toggles.
- Auth profile responses are enriched with additive `account` + `profile_page` context when available.
