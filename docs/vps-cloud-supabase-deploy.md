# VPS Deployment With Cloud Supabase

This app should not run a local PostgreSQL container in production.

The backend already uses `supabase-py` and expects a hosted Supabase project via:

```env
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_KEY=YOUR_SUPABASE_SERVICE_ROLE_KEY
FLASK_SECRET_KEY=replace-with-a-long-random-secret
```

Put those values in:

```text
tradescenter-backend/.env
```

Then apply the database schema to the cloud Supabase project:

1. Run `tradescenter-backend/supabase/schema.sql`
2. Run `tradescenter-backend/supabase/migrations/20260423_01_platform_v15_identity_billing_verification.sql`

If the project was only partially initialized and is missing tables such as `public.profiles`, run this reconciliation migration instead:

3. Run `tradescenter-backend/supabase/migrations/20260423_02_reconcile_missing_tables.sql`

After that, deploy with:

```bash
docker compose up --build -d
```

Expected runtime shape:

- `frontend` container
- `backend` container
- no local `db` container

Validation query for the target Supabase project:

```sql
select to_regclass('public.profiles');
```

If that query returns `null`, the remote schema has not been applied yet.
