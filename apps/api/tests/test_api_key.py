from jevops.auth.api_key import generate_api_key, hash_api_key, parse_api_key, verify_api_key


def test_generate_api_key_format():
    full_key, prefix, secret = generate_api_key("live")
    assert full_key.startswith("jvo_live_")
    assert prefix.startswith("jvo_live_")
    assert len(secret) == 32
    assert full_key == f"{prefix}_{secret}"


def test_generate_api_key_test_env():
    full_key, _prefix, _secret = generate_api_key("test")
    assert full_key.startswith("jvo_test_")


def test_hash_and_verify():
    _, _, secret = generate_api_key()
    pepper = "test-pepper"
    h = hash_api_key(secret, pepper)
    assert verify_api_key(secret, pepper, h)
    assert not verify_api_key("wrong-secret", pepper, h)
    assert not verify_api_key(secret, "wrong-pepper", h)


def test_parse_api_key():
    full_key, prefix, secret = generate_api_key("live")
    result = parse_api_key(full_key)
    assert result is not None
    assert result[0] == prefix
    assert result[1] == secret


def test_parse_invalid_key():
    assert parse_api_key("invalid") is None
    assert parse_api_key("bad_key") is None
    assert parse_api_key("") is None
