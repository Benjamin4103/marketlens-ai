# Setup Guide

Two paths: Docker (fastest) or manual local setup (what was actually used to
build and test this project, documented exactly).

## Option A: Docker

```bash
cp backend/.env.example backend/.env
docker compose up --build
```
Frontend at `http://localhost:5173`, API at `http://localhost:8000`.

## Option B: Manual local setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 16 with build tools to compile `pgvector` (or a package/image
  that already includes it)
- Redis (optional at this stage — wired for a future Celery upgrade, not
  required for the current pipeline)

### 1. PostgreSQL + pgvector

```bash
sudo apt-get install -y postgresql postgresql-contrib postgresql-server-dev-16 build-essential git

git clone --branch v0.7.4 https://github.com/pgvector/pgvector.git
cd pgvector && make -j4 && sudo make install

sudo service postgresql start
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
sudo -u postgres createdb marketlens
sudo -u postgres psql -d marketlens -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 2. Redis (optional)
```bash
sudo apt-get install -y redis-server
redis-server --daemonize yes
```

### 3. Backend

```bash
cd backend
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

cp .env.example .env
# defaults work as-is: DEMO_MODE=true, DB on localhost:5432

./venv/bin/alembic upgrade head

./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Verify: `curl http://localhost:8000/api/health` should return
`{"status": "ok", ..., "database": "connected"}`.

Run the test suite:
```bash
./venv/bin/pytest tests/ -v
```

### 4. Frontend

```bash
cd frontend
npm install
cp .env.example .env   # or create one: VITE_API_BASE=http://localhost:8000/api
npm run dev -- --host 0.0.0.0 --port 5173
```
Open `http://localhost:5173`, register an account, and start research.

### 5. Enabling live (non-demo) research

By default `DEMO_MODE=true` in `backend/.env`, and the pipeline uses a
deterministic synthetic dataset. Real agents (LangGraph + Gemini, using
Gemini's Google Search grounding tool for live web sources) are implemented
in `backend/app/agents/`. To use them:

1. Get a Gemini API key from https://aistudio.google.com/apikey.
2. Add it to `backend/.env`: `GEMINI_API_KEY=your-key-here`.
3. **Verify the key works first**, in isolation, before starting the app:
   ```bash
   cd backend
   ./venv/bin/python scripts/test_gemini_key.py
   ```
   This checks both plain generation and grounded search (the latter is
   what the research agents actually depend on). Fix any errors it reports
   before continuing — it's much faster to debug here than inside a
   background research job.
4. Set `DEMO_MODE=false` in `backend/.env`.
5. Restart the backend (`./venv/bin/uvicorn app.main:app ...`) and run a
   research query as normal — `GET /api/health` should now show
   `"demo_mode": false`.

If the real pipeline fails partway through a research job (bad key,
grounding disabled, rate limit, etc.), the orchestrator catches the failure,
logs it, and **falls back to the demo dataset** for that job rather than
leaving it stuck — check `backend`'s server logs if a report looks
suspiciously like demo data when you expected live results.

Note: market size / CAGR figures are intentionally left blank
("Insufficient reliable data found.") in live mode rather than risk
extracting an unverified number from a search snippet.

## Common issues

- **`passlib`/`bcrypt` error on register/login**: pin `bcrypt==4.0.1` — newer
  bcrypt releases changed an internal API passlib 1.7.x expects.
- **`ModuleNotFoundError: No module named 'app'` running pytest**: run pytest
  from the `backend/` directory, or ensure `pytest.ini` has `pythonpath = .`
  (already included in this repo).
- **asyncpg "another operation is in progress" in tests**: the async engine
  uses `NullPool` (see `app/db/session.py`) specifically so a fresh event
  loop per test doesn't reuse a stale pooled connection.
