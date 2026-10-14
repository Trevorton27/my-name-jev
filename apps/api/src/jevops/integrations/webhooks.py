from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


def sign_payload(payload: dict[str, Any], secret: str) -> str:
    body = json.dumps(payload, default=str)
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()


def verify_signature(payload_bytes: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
