# MarketLens AI — Build Progress

## Status: Demo mode COMPLETE + verified. Real agent layer (Gemini) IMPLEMENTED but NOT live-tested (sandbox network can't reach Google's API).

## Environment (start these each new session)
```
service postgresql start
redis-server --daemonize yes
cd backend && setsid nohup ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/uvicorn.log 2>&1 < /dev/null &
cd frontend && setsid nohup npm run dev -- --host 0.0.0.0 --port 5173 > /tmp/vite.log 2>&1 < /dev/null &
```
This sandbox is ephemeral — if `/home/claude/marketlens-ai` is missing on a
new session, restore from `/mnt/user-data/outputs/marketlens-ai.tar.gz`
(re-export a fresh one after any further changes).

## What changed in this session: real Gemini-backed agents
- Added `backend/app/services/llm_client.py`: provider-agnostic LLM
  interface, `GeminiClient` implementation using `google-genai` SDK with
  Gemini's built-in `GoogleSearch` grounding tool (so no separate search
  API key is needed for real web sources)
- Added `backend/app/agents/`: planner, research (web+news via grounding),
  competitor (discovery + structured extraction), trends, sentiment,
  analyst+strategy (synthesis), evidence (confidence/risk scoring)
- Added `backend/app/agents/graph.py`: LangGraph `StateGraph` wiring all
  agents into one pipeline (`run_real_pipeline`), returning the exact same
  dataset shape as `demo_data.generate_demo_dataset` so it's a drop-in
  swap in the orchestrator
- Updated `app/core/config.py`: added `GEMINI_API_KEY`/`GEMINI_MODEL`
  settings, `effective_demo_mode` now checks the configured provider's key
- Updated `app/services/orchestrator.py`: when `DEMO_MODE=false`, calls
  `run_real_pipeline`; on any failure (bad key, no grounding results, etc.)
  catches it, logs it, and falls back to the demo dataset for that job
  rather than leaving it stuck
- Updated `app/services/report_builder.py`: uses the real pipeline's
  `market_overview` text directly when present
- Added `backend/scripts/test_gemini_key.py`: standalone script to sanity
  check a Gemini key (plain + grounded generation) before running the full
  app — the fast way to debug key/SDK issues
- Updated README.md / SETUP.md with the live-mode instructions

## IMPORTANT — not verified live, and why
This sandbox's network egress explicitly blocks
`generativelanguage.googleapis.com` ("Host not in allowlist" — confirmed via
direct curl test, not a guess). So the real agent pipeline **could not be
run against a live key from this environment**, even with a valid one
supplied. What WAS verified:
- All new code imports cleanly, no syntax/type errors
- Full pytest suite (5/5) still passes in demo mode — the fallback logic in
  orchestrator.py correctly preserves 100% of previously-working demo-mode
  behavior
- Live demo-mode smoke test re-run post-integration: still completes,
  still produces 19-section reports
- `test_gemini_key.py` correctly detects a missing key and exits cleanly

**What genuinely has NOT been verified:** whether the Gemini calls
themselves work correctly against a real key — the exact prompt/schema
round-trips, whether `generate_json` reliably parses Gemini's JSON mode
output, whether grounding_metadata extraction matches the actual SDK
response shape at runtime, latency of a full 5-competitor pipeline run,
etc. The user must run `scripts/test_gemini_key.py` first, then a full
research query, on their own machine, and report back if anything breaks.

## Known rough edges to watch for (found via research, not direct testing)
- Newer Gemini API keys (`AQ.` prefix, "Authentication Keys") have had
  reported compatibility issues with some SDK versions/endpoints (401
  ACCESS_TOKEN_TYPE_UNSUPPORTED on certain calls). Pinned
  `google-genai==2.22.0` in requirements.txt as the version tested at
  install time in this sandbox — if the user hits auth errors,
  `pip install --upgrade google-genai` first.
- Gemini's JSON mode (`response_mime_type="application/json"`) is generally
  reliable but `generate_json()` has a defensive fallback for stray code
  fences; if agents produce malformed JSON, check the raw response text.

## Everything else (backend core, frontend, demo mode) — unchanged from
before, still complete and verified as described in prior sessions:
16-table schema, 19 API endpoints, full pipeline, PDF/MD/JSON export,
What Changed? diffing, React/Vite/TS/Tailwind frontend with EvidenceRing
design system, Docker config, docs.

## NEXT STEPS if resuming
1. User tests `scripts/test_gemini_key.py` and a real research query
   locally, reports back any failures
2. Fix whatever breaks (most likely candidates: JSON parsing edge cases in
   generate_json, grounding_metadata attribute path differences, or the
   AQ-key SDK compatibility issue noted above)
3. Consider adding per-claim source_ids linkage (currently empty in live
   mode) if citation-level traceability in the UI matters for the user
4. Re-export the archive after changes: `tar czf marketlens-ai.tar.gz
   marketlens-ai` (excluding node_modules/venv) and copy to
   `/mnt/user-data/outputs/`
