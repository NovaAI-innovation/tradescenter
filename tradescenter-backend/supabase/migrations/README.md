# Supabase SQL Migrations

Use additive, versioned SQL files in this directory for all schema changes after base bootstrap.

## Convention
- Filename: `YYYYMMDD_NN_short_description.sql`
- Example: `20260423_01_platform_v15_identity_billing_verification.sql`
- `NN` increments for multiple migrations on the same day.

## Execution order
1. Run `../schema.sql` only for base database bootstrap.
2. Run migration files here in filename order.

## Rule
Do not append feature-specific schema changes directly to `schema.sql`; create a new migration file instead.
