from httpx import ASGITransport, AsyncClient

from jevops.config import SecuritySettings, Settings
from jevops.main import create_app


async def _post_reset(settings: Settings, headers: dict[str, str] | None = None) -> int:
    transport = ASGITransport(app=create_app(settings))
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/v1/demo/reset", headers=headers or {})
    return response.status_code


async def test_reset_disabled_without_configured_token(client: AsyncClient):
    response = await client.post("/v1/demo/reset", headers={"X-Demo-Reset-Token": "anything"})
    assert response.status_code == 403


async def test_reset_rejects_missing_or_wrong_token():
    settings = Settings(environment="test", security=SecuritySettings(demo_reset_token="s3cret"))
    assert await _post_reset(settings) == 401
    assert await _post_reset(settings, {"X-Demo-Reset-Token": "wrong"}) == 401
