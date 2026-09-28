"""
Quick standalone sanity check for your Gemini API key -- run this BEFORE
starting the full app, so a bad key or SDK version mismatch is obvious
immediately rather than buried in a background pipeline failure.

Usage:
    cd backend
    ./venv/bin/python scripts/test_gemini_key.py

Requires GEMINI_API_KEY to be set in backend/.env (or the environment).
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


async def main():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("GEMINI_API_KEY is not set in backend/.env -- add it and re-run.")
        sys.exit(1)

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    print(f"Testing Gemini API key against model={model!r} ...")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    # 1. Plain generation -- confirms the key authenticates at all.
    try:
        resp = await client.aio.models.generate_content(
            model=model, contents="Reply with exactly: OK"
        )
        print(f"[1/2] Plain generation: OK -- model replied: {resp.text!r}")
    except Exception as exc:
        print(f"[1/2] Plain generation FAILED: {exc}")
        print(
            "\nIf this mentions 401/UNAUTHENTICATED or ACCESS_TOKEN_TYPE_UNSUPPORTED, "
            "the AQ.-prefixed key format has had rough edges with some SDK/endpoint "
            "combinations. Try: pip install --upgrade google-genai, or generate a "
            "fresh key at https://aistudio.google.com/apikey."
        )
        sys.exit(1)

    # 2. Grounded generation with Google Search -- this is what the real
    # research agents depend on for live web sources.
    try:
        resp = await client.aio.models.generate_content(
            model=model,
            contents="What is today's date and one recent AI industry headline?",
            config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())]),
        )
        grounded = bool(resp.candidates[0].grounding_metadata.grounding_chunks)
        print(f"[2/2] Grounded search: OK -- got {'grounded' if grounded else 'ungrounded'} response")
        print(f"      Response: {resp.text[:200]}")
        if not grounded:
            print(
                "      NOTE: no grounding chunks returned. Google Search grounding "
                "may need to be enabled for your API key/project -- check "
                "https://ai.google.dev/gemini-api/docs/grounding"
            )
    except Exception as exc:
        print(f"[2/2] Grounded search FAILED: {exc}")
        print(
            "\nThe research agents (web/news/competitor/trend/sentiment) all depend "
            "on grounded search working. Plain generation succeeded, so the key "
            "itself is valid -- this is likely a grounding-specific permission or "
            "API version issue. Check the link above."
        )
        sys.exit(1)

    print("\nAll checks passed. Set DEMO_MODE=false in backend/.env and restart the server.")


if __name__ == "__main__":
    asyncio.run(main())
