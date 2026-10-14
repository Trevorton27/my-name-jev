from __future__ import annotations

from jevops.database.repositories.base import BaseRepository
from jevops.models.api_key import APIKey


class APIKeyRepository(BaseRepository[APIKey]):
    model = APIKey
