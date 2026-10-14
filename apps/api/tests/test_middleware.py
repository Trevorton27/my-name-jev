import pytest


@pytest.mark.asyncio
async def test_correlation_id_generated(client):
    resp = await client.get("/health")
    assert "x-correlation-id" in resp.headers


@pytest.mark.asyncio
async def test_correlation_id_echoed(client):
    resp = await client.get("/health", headers={"X-Correlation-ID": "test-123"})
    assert resp.headers["x-correlation-id"] == "test-123"


@pytest.mark.asyncio
async def test_secure_headers(client):
    resp = await client.get("/health")
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
