# Supabase Migration Notes

## What Changed
- Backend persistence moved from SQLite + SQLAlchemy to Supabase Postgres via `supabase-py`.
- Active API route modules now query Supabase tables directly:
  - `src/routes/user.py`
  - `src/routes/contractors.py`
  - `src/routes/projects.py`
  - `src/routes/reviews.py`
  - `src/routes/auth.py`
  - `src/routes/social.py`
  - `src/routes/messages.py`
  - `src/routes/admin.py`
  - `src/routes/tiers.py`
- Flask app startup no longer initializes SQLAlchemy models.

## New Backend Setup
1. Copy `.env.example` to `.env` in `tradescenter-backend`.
2. Fill `SUPABASE_URL` and `SUPABASE_KEY`.
3. Run the schema in your Supabase SQL editor: `tradescenter-backend/supabase/schema.sql`.
4. Install dependencies and run the API:
   - `pip install -r requirements.txt`
   - `python src/main.py`
5. Optional seed data:
   - `python src/seed_data.py`

## Auth + RBAC + Social Features
- Supabase Auth endpoints:
  - `POST /api/auth/register`
  - `POST /api/auth/login`
  - `GET /api/auth/me`
  - `PUT /api/auth/profile`
- Social feed endpoints:
  - `GET /api/feed`
  - `POST /api/posts`
  - `GET /api/posts/:id`
  - `POST /api/posts/:id/comments`
  - `POST /api/comments/:id/replies`
  - `POST/DELETE /api/reactions`
  - `POST /api/posts/:id/share`
- Messaging endpoints:
  - `GET/POST /api/messages/conversations`
  - `GET/POST /api/messages/conversations/:id/messages`
- Tier and admin endpoints:
  - `GET /api/contractor/tier/status`
  - `POST /api/contractor/tier/checkout-demo`
  - `GET /api/admin/moderation`
  - `POST /api/admin/moderation/action`

## Frontend Rebuild
- `tradescenter-frontend` was recreated as a new React + Vite app.
- UI includes a redesigned command-style dashboard and consumes live API endpoints:
  - `/api/health`
  - `/api/contractors/featured`
  - `/api/projects`
  - `/api/reviews`
- Set `VITE_API_BASE_URL` in `tradescenter-frontend/.env`.
