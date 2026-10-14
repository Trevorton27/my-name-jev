from jevops.retry import RetryConfig


def test_retry_config_defaults():
    cfg = RetryConfig()
    assert cfg.max_retries == 3
    assert cfg.backoff_base == 1.0
    assert 429 in cfg.retryable_status_codes


def test_delay_exponential():
    cfg = RetryConfig(backoff_base=1.0, backoff_max=30.0)
    assert cfg.delay(0) == 1.0
    assert cfg.delay(1) == 2.0
    assert cfg.delay(2) == 4.0
    assert cfg.delay(3) == 8.0


def test_delay_capped():
    cfg = RetryConfig(backoff_base=1.0, backoff_max=10.0)
    assert cfg.delay(10) == 10.0
