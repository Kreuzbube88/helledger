from app.auth.rate_limit import RateLimiter


def test_allows_under_limit():
    rl = RateLimiter(max_attempts=3, window_minutes=15)
    assert rl.is_blocked("1.2.3.4") is False
    rl.record_failure("1.2.3.4")
    assert rl.is_blocked("1.2.3.4") is False
    rl.record_failure("1.2.3.4")
    assert rl.is_blocked("1.2.3.4") is False
    rl.record_failure("1.2.3.4")
    assert rl.is_blocked("1.2.3.4") is True  # now at limit


def test_blocks_over_limit():
    rl = RateLimiter(max_attempts=3, window_minutes=15)
    rl.record_failure("10.0.0.1")
    rl.record_failure("10.0.0.1")
    rl.record_failure("10.0.0.1")
    assert rl.is_blocked("10.0.0.1") is True


def test_different_ips_independent():
    rl = RateLimiter(max_attempts=2, window_minutes=15)
    rl.record_failure("192.168.1.1")
    rl.record_failure("192.168.1.1")
    assert rl.is_blocked("192.168.1.1") is True
    assert rl.is_blocked("192.168.1.2") is False


def test_login_rate_limit_returns_429(client):
    """Verify the wiring: 5 failed logins → 429 on 6th."""
    for _ in range(5):
        client.post("/api/auth/login", json={"email": "noexist@example.com", "password": "wrong"})
    r = client.post("/api/auth/login", json={"email": "noexist@example.com", "password": "wrong"})
    assert r.status_code == 429
    assert r.json()["detail"] == "too_many_requests"
