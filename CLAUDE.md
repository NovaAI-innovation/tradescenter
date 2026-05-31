# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Make smallest changes possible.

Do not pollute your context. 

Remain in task scope. 

---

## Commands

### Frontend (`tradescenter-frontend/`)

```bash
npm run dev        # dev server on port 5174 (configured in vite.config.js)
npm run build      # production build → dist/
npm run preview    # serve the production build locally
```

No test runner or linter is configured. There is no type-checking (no TypeScript).

### Backend (`tradescenter-backend/`)

```bash
# Activate the venv first
source venv/Scripts/activate   # Windows Git Bash
python -m flask --app src/main run --port 5000 --debug

# Seed legacy tables (public.users, not public.profiles — see schema note below)
python -c "from src.seed_data import upsert_seed_data; upsert_seed_data()"
```

Backend requires a `.env` file — copy `.env.example` and fill in:
```
SUPABASE_URL=...
SUPABASE_KEY=...        # use the service role key for server-side access
FLASK_SECRET_KEY=...
```

Frontend requires `tradescenter-frontend/.env`:
```
VITE_API_BASE_URL=http://localhost:5000/api
```

---

## Architecture

### Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, React Router v6, Vite, Framer Motion, Lucide React |
| Backend | Flask 3, flask-cors, PyJWT, python-dotenv |
| Database | Supabase (PostgreSQL) via `supabase-py` client |
| Auth | Supabase Auth (JWTs) — validated server-side on every protected route |

### Frontend Structure

The entire frontend is a **single file** — `src/App.jsx` — with no component subdirectory. All pages, hooks, and the shell are defined inline:

- `useAuth()` — checks `localStorage` for `tc_access_token`, calls `GET /api/auth/me` on mount
- `Shell` — top-level component. Renders the topbar, conditionally renders `<AuthPanel>` for unauthenticated users, then renders `<Routes>`
- Pages: `HomePage`, `AboutPage`, `SupportPage`, `PricingPage`, `FeedPage`, `MessagesPage`, `ContractorStudio`, `AdminPage`

API calls live in `src/api/client.js`. The base URL defaults to `http://localhost:5000/api` and is overridden by `VITE_API_BASE_URL`. The JWT token is stored in and read from `localStorage` under the key `tc_access_token`.

### Backend Structure

Flask app in `src/main.py` registers nine blueprints, all mounted at `/api`:

| Blueprint | File | Key prefix |
|---|---|---|
| `auth_bp` | `routes/auth.py` | `/api/auth/` |
| `social_bp` | `routes/social.py` | `/api/feed`, `/api/posts`, `/api/categories`, `/api/reactions`, `/api/shares` |
| `messages_bp` | `routes/messages.py` | `/api/messages/` |
| `tiers_bp` | `routes/tiers.py` | `/api/contractor/tier/` |
| `admin_bp` | `routes/admin.py` | `/api/admin/` |
| `user_bp`, `contractors_bp`, `projects_bp`, `reviews_bp` | routes/ | `/api/` |

Auth middleware is in `src/authz.py`. The two decorators used throughout routes are:
- `@require_auth` — resolves JWT → Supabase auth user → `profiles` row, sets `g.current_profile`
- `@require_roles("admin")` / `@require_roles("contractor")` — same resolution plus role check

`src/utils.py` provides `error_response()`, `normalize_record()` (serialises datetime values), and `parse_int()`.

### Database Schema

The Supabase schema (`tradescenter-backend/supabase/schema.sql`) contains **two generations** of tables:

**Legacy tables** (from the original listing platform — used by `seed_data.py` only):
`users`, `contractors`, `projects`, `project_milestones`, `project_files`, `reviews`

**Active tables** (used by all current routes):
`profiles`, `posts`, `post_media`, `comments`, `reactions`, `shares`, `conversations`, `conversation_participants`, `messages`, `contractor_tier_subscriptions`

The `profiles` table is the central identity record. It is auto-created on first login/register via `get_or_create_profile()` in `authz.py`. Key columns: `auth_user_id` (links to Supabase Auth), `role` (`user` | `contractor` | `admin`), `contractor_tier` (`free` | `pro` | `platinum`), `is_suspended`.

Contractor tier limits are computed in `authz.get_tier_limits()` — not stored in the DB. Stripe is not wired; the demo checkout endpoint (`/api/contractor/tier/checkout-demo`) directly updates the `profiles` row.

### Rank Scoring

Post feed ordering uses a computed `rank_score` built in `social.py`. It is not stored — calculated at query time from reaction counts, shares, comments, and a `promoted` boost multiplier. The score is currently returned to the client and displayed in the feed UI (this is a known UX issue).

### Role System

Three roles enforced at the backend: `user`, `contractor`, `admin`. Role is set at registration and stored in `profiles.role`. The `admin` role cannot be self-assigned — registration forces `admin` → `user`. Admin users can manually set tiers via `POST /api/admin/moderation/action`.

---

## Known Issues (Active)

- `<AuthPanel>` renders on every route for unauthenticated users — it is not scoped to `/`. This means the login form appears above the fold on `/pricing`, `/about`, `/support`, and `/get-inspired`.
- Navigation is hidden entirely at ≤860px viewport with no mobile menu fallback.
- The feed error state surfaces raw PostgREST JSON (including schema details) directly to users when the backend is unavailable.
- `page-metadata` debug block (API status + persistence mode) is rendered inline on the home page.
- Post `rank_score` is exposed in the feed card UI — it is an internal signal, not user-facing information.
