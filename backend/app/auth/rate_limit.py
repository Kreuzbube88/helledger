# In-memory rate limiter. Works correctly for single-process deployments.
# For multi-worker (Gunicorn) or multi-replica, replace with Redis-backed store.
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from threading import Lock


class RateLimiter:
    def __init__(self, max_attempts: int = 5, window_minutes: int = 15) -> None:
        self._max = max_attempts
        self._window = timedelta(minutes=window_minutes)
        self._attempts: dict[str, list[datetime]] = defaultdict(list)
        self._lock = Lock()

    def _prune(self, key: str, now: datetime) -> None:
        cutoff = now - self._window
        self._attempts[key] = [t for t in self._attempts[key] if t > cutoff]

    def is_blocked(self, key: str) -> bool:
        """Returns True if this key has exceeded the rate limit."""
        now = datetime.now(timezone.utc)
        with self._lock:
            self._prune(key, now)
            return len(self._attempts[key]) >= self._max

    def record_failure(self, key: str) -> None:
        """Record a failed attempt for this key."""
        now = datetime.now(timezone.utc)
        with self._lock:
            self._prune(key, now)
            self._attempts[key].append(now)

    def reset(self) -> None:
        with self._lock:
            self._attempts.clear()


_login_limiter = RateLimiter(max_attempts=5, window_minutes=15)
