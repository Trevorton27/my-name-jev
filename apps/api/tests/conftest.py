import pytest
from httpx import ASGITransport, AsyncClient

from jevops.config import Settings
from jevops.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(
        environment="test",
        debug=True,
        log_format="console",
    )


@pytest.fixture
def app(settings: Settings):
    return create_app(settings)


@pytest.fixture
async def client(app) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
