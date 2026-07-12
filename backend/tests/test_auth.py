"""
Basic auth endpoint tests.

Run with:  pytest backend/tests/ -v
"""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.init_db import init_db


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_and_login():
    """
    Integration smoke-test: register then get /me
    Uses the real PostgreSQL test database from CI environment.
    """
    # Create all tables before running tests
    await init_db()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Register
        reg = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass1",
        })
        assert reg.status_code == 201, reg.text
        token = reg.json()["access_token"]

        # Get profile
        me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me.status_code == 200
        assert me.json()["email"] == "test@example.com"
