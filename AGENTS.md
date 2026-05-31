# Repository Guidelines

## Project Structure & Module Organization
`tradescenter-frontend/` contains the Vite + React app. Keep UI code in `src/`, API helpers in `src/api/`, shared hooks in `src/hooks/`, config in `src/config/`, and static images in `images/`. `tradescenter-backend/` contains the Flask API: route blueprints live in `src/routes/`, request/domain models in `src/models/`, and shared integrations such as Supabase and Stripe in `src/*_client.py`. Supabase SQL lives in `tradescenter-backend/supabase/` with ordered migrations under `migrations/`. Top-level `docs/` holds product, architecture, and deployment notes.

## Build, Test, and Development Commands
Frontend:
- `cd tradescenter-frontend && npm install` installs dependencies.
- `npm run dev` starts the Vite dev server.
- `npm run build` creates the production bundle.
- `npm run preview` serves the built frontend locally.

Backend:
- `cd tradescenter-backend && pip install -r requirements.txt` installs Flask/Supabase dependencies.
- `python -m flask --app src.main run --host 0.0.0.0 --port 5000` runs the API locally.

Infrastructure:
- `docker compose up --build` starts the frontend and backend containers.
- `docker compose -f docker-compose.local.yml up -d` starts the local Supabase/PostgREST stack.

## Coding Style & Naming Conventions
Match the existing codebase. React files use 2-space indentation, double quotes, PascalCase component names (`SafeMedia.jsx`), and camelCase hooks/utilities. Python uses 4-space indentation, snake_case function names, and thin route modules grouped by resource (`routes/auth.py`, `routes/billing.py`). Prefer small edits over new abstractions, and keep SQL migration filenames timestamp-prefixed.

## Testing Guidelines
There is no committed automated test suite yet. For backend changes, at minimum verify `GET /api/health` and the affected endpoints against the local stack. For frontend changes, run `npm run build` and smoke-test the impacted screen in the browser. Add focused tests with any non-trivial feature or bug fix, and keep test files near the code they validate or under a `tests/` directory.

## Commit & Pull Request Guidelines
Use concise, decision-oriented commits. This repo's workflow expects Lore-style messages: an intent line followed by trailers such as `Constraint:`, `Rejected:`, `Confidence:`, and `Tested:` when they add context. Pull requests should summarize the user-visible change, list validation performed, link the issue or plan doc, and include screenshots for UI changes. Call out schema, env, or migration impacts explicitly.
