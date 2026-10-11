"""Tiny thread-safe TTL cache for expensive read endpoints.

Used for recommendation results, which are costly full-table scans.
Entries are versioned per user / per team project so profile writes
invalidate instantly without waiting for TTL expiry.

Single-process by design. For multi-replica deployments, swap this module
for a Redis-backed implementation with the same function signatures.
"""

import threading
import time

_lock = threading.Lock()
_store: dict[str, tuple[object, float]] = {}
_versions: dict[str, int] = {}

MAX_ENTRIES = 2000


def _evict_expired(now: float) -> None:
    expired = [k for k, (_, exp) in _store.items() if exp <= now]
    for k in expired:
        del _store[k]


def get(key: str):
    now = time.time()
    with _lock:
        entry = _store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at <= now:
            del _store[key]
            return None
        return value


def set(key: str, value: object, ttl_seconds: int) -> None:
    if ttl_seconds <= 0:
        return
    with _lock:
        if len(_store) >= MAX_ENTRIES:
            _evict_expired(time.time())
        _store[key] = (value, time.time() + ttl_seconds)


def bump_version(scope: str) -> None:
    with _lock:
        _versions[scope] = _versions.get(scope, 0) + 1


def version(scope: str) -> int:
    with _lock:
        return _versions.get(scope, 0)


def user_scope(user_id: int) -> str:
    return f"user:{user_id}"


def project_scope(project_id: int) -> str:
    return f"team-project:{project_id}"


def clear() -> None:
    """Test helper: empty the cache and all versions."""
    with _lock:
        _store.clear()
        _versions.clear()
