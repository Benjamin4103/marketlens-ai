import asyncio
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.session import get_db, AsyncSessionLocal


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client):
    email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    password = "testpass123"
    await client.post("/api/auth/register", json={"email": email, "password": password, "full_name": "Test User"})
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
