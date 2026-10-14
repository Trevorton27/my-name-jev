from __future__ import annotations

import hashlib
import secrets


def generate_api_key(environment: str = "test") -> tuple[str, str, str]:
    """Generate an API key. Returns (full_key, prefix, secret)."""
    env_label = "live" if environment == "live" else "test"
    prefix = secrets.token_hex(4)
    secret = secrets.token_hex(16)
    full_key = f"jvo_{env_label}_{prefix}_{secret}"
    return full_key, f"jvo_{env_label}_{prefix}", secret


def hash_api_key(secret: str, pepper: str) -> str:
    """SHA-256 hash of secret + pepper."""
    return hashlib.sha256(f"{secret}{pepper}".encode()).hexdigest()


def verify_api_key(secret: str, pepper: str, stored_hash: str) -> bool:
    """Verify a secret against a stored hash."""
    return hash_api_key(secret, pepper) == stored_hash


def parse_api_key(full_key: str) -> tuple[str, str] | None:
    """Parse full key into (prefix, secret). Returns None if malformed."""
    # Format: jvo_{env}_{8char}_{32char}
    parts = full_key.split("_", 3)
    if len(parts) != 4 or parts[0] != "jvo":
        return None
    prefix = f"{parts[0]}_{parts[1]}_{parts[2]}"
    secret = parts[3]
    return prefix, secret
