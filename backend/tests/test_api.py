import asyncio
import uuid

import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"


@pytest.mark.asyncio
async def test_register_and_login(client):
    email = f"pytest-auth-{uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post(
        "/api/auth/register", json={"email": email, "password": "testpass123", "full_name": "PyTest"}
    )
    assert resp.status_code == 201

    # Duplicate registration should fail
    resp2 = await client.post(
        "/api/auth/register", json={"email": email, "password": "testpass123", "full_name": "PyTest"}
    )
    assert resp2.status_code == 400

    resp3 = await client.post("/api/auth/login", json={"email": email, "password": "testpass123"})
    assert resp3.status_code == 200
    assert "access_token" in resp3.json()

    # Wrong password
    resp4 = await client.post("/api/auth/login", json={"email": email, "password": "wrong"})
    assert resp4.status_code == 401


@pytest.mark.asyncio
async def test_research_requires_auth(client):
    resp = await client.post("/api/research", json={"query": "Test Market"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_full_research_pipeline(client, auth_headers):
    # Create
    resp = await client.post(
        "/api/research",
        json={"query": "Global SaaS Market", "geography": "Global", "depth": "quick"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    job = resp.json()
    job_id = job["id"]
    assert job["status"] == "pending"

    # Run (background task executes synchronously enough within the test's
    # event loop for a demo-mode job, but poll defensively)
    resp = await client.post(f"/api/research/{job_id}/run", headers=auth_headers)
    assert resp.status_code == 200

    for _ in range(20):
        status_resp = await client.get(f"/api/research/{job_id}/status", headers=auth_headers)
        status = status_resp.json()["status"]
        if status in ("completed", "failed"):
            break
        await asyncio.sleep(0.2)

    assert status == "completed", status_resp.json()

    # Sources
    resp = await client.get(f"/api/research/{job_id}/sources", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) > 0

    # Competitors
    resp = await client.get(f"/api/research/{job_id}/competitors", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) > 0

    # Trends
    resp = await client.get(f"/api/research/{job_id}/trends", headers=auth_headers)
    assert resp.status_code == 200

    # Report
    resp = await client.get(f"/api/research/{job_id}/report", headers=auth_headers)
    assert resp.status_code == 200
    report = resp.json()
    assert "executive_summary" in report["sections"]
    assert report["overall_confidence"] > 0

    # Export JSON
    resp = await client.post(f"/api/research/{job_id}/export?fmt=json", headers=auth_headers)
    assert resp.status_code == 200

    # Export Markdown
    resp = await client.post(f"/api/research/{job_id}/export?fmt=markdown", headers=auth_headers)
    assert resp.status_code == 200
    assert b"# " in resp.content

    # Export PDF
    resp = await client.post(f"/api/research/{job_id}/export?fmt=pdf", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.content[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_what_changed_single_run_note(client, auth_headers):
    unique_query = f"Unique Single Run Market {uuid.uuid4().hex[:8]}"
    resp = await client.post(
        "/api/research", json={"query": unique_query}, headers=auth_headers
    )
    job = resp.json()
    project_id = job["project_id"]
    job_id = job["id"]

    await client.post(f"/api/research/{job_id}/run", headers=auth_headers)
    for _ in range(20):
        status_resp = await client.get(f"/api/research/{job_id}/status", headers=auth_headers)
        if status_resp.json()["status"] in ("completed", "failed"):
            break
        await asyncio.sleep(0.2)

    resp = await client.get(f"/api/research/{project_id}/what-changed", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["note"] is not None  # only one run — should explain nothing to compare yet
