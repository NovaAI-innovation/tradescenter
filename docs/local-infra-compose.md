# Local Infra Compose

Use the local override when you want the app plus local development infrastructure:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up --build -d
```

This currently adds a lightweight local Supabase-compatible REST layer:

- `supabase-db`: local Postgres initialized from `tradescenter-backend/supabase/schema.sql` and migrations
- `supabase-rest`: PostgREST over the `public` schema
- `supabase-api`: local gateway that exposes Supabase-style `/rest/v1` routes on `http://localhost:54321`

The backend is overridden to use the internal URL `http://supabase-api:8000` and the local service-role key.

Default local values:

```env
LOCAL_SUPABASE_PORT=54321
LOCAL_SUPABASE_DB=postgres
LOCAL_SUPABASE_DB_USER=postgres
LOCAL_SUPABASE_DB_PASSWORD=postgres
LOCAL_SUPABASE_JWT_SECRET=tradescenter-local-jwt-secret-with-at-least-32-chars
LOCAL_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ0cmFkZXNjZW50ZXItbG9jYWwiLCJleHAiOjQxMDI0NDQ4MDAsInJvbGUiOiJhbm9uIn0.dQNrQGKoS_yhkkkKvbR-C5zoAxgDV1vvMNHmfv2h-Y0
LOCAL_SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ0cmFkZXNjZW50ZXItbG9jYWwiLCJleHAiOjQxMDI0NDQ4MDAsInJvbGUiOiJzZXJ2aWNlX3JvbGUifQ.urSsVDuWvCfqCWVdZuCgJgRb37ZkLPdrAqOqe5Ibznk
```

To reset the local database, stop the stack and remove the local infra volume:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml down -v
```

Production deployment should continue to use `docker-compose.yml` with hosted Supabase credentials in `tradescenter-backend/.env`.
