"""Tests for scale hardening: rate limiting, pagination totals, caching."""

from app.core import cache as result_cache
from tests.conftest import create_user_with_token


class TestRateLimiting:
    def test_auth_endpoints_limited(self, client, monkeypatch):
        from app.core.config import get_settings

        settings = get_settings()
        monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
        monkeypatch.setattr(settings, "RATE_LIMIT_AUTH_PER_MINUTE", 3)

        for _ in range(3):
            client.post(
                "/api/v1/auth/login",
                json={"email": "nobody@example.com", "password": "password123"},
            )
        limited = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "password123"},
        )
        assert limited.status_code == 429
        assert limited.headers.get("Retry-After") == "60"

    def test_health_never_limited(self, client, monkeypatch):
        from app.core.config import get_settings

        settings = get_settings()
        monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
        monkeypatch.setattr(settings, "RATE_LIMIT_DEFAULT_PER_MINUTE", 1)
        assert client.get("/health").status_code == 200
        assert client.get("/health").status_code == 200


class TestPaginationTotals:
    def test_users_total_header(self, client):
        headers = create_user_with_token(client, "counter1", "counter1@example.com")
        response = client.get("/api/v1/users/", headers=headers)
        assert response.status_code == 200
        assert int(response.headers["X-Total-Count"]) >= 1

    def test_team_projects_total_header(self, client):
        headers = create_user_with_token(client, "counter2", "counter2@example.com")
        response = client.get("/api/v1/team-projects", headers=headers)
        assert response.status_code == 200
        assert "X-Total-Count" in response.headers


class TestRecommendationCache:
    def test_recommendations_cached_and_invalidated(self, client):
        from tests.conftest import login_user, register_user

        for uname in ("cachea", "cacheb", "cachec"):
            register_user(client, uname, f"{uname}@example.com")
        tokens = {}
        for uname in ("cachea", "cacheb", "cachec"):
            tokens[uname] = login_user(client, f"{uname}@example.com").json()[
                "access_token"
            ]
        # Give every profile an embedding so matching actually computes.
        for uname, token in tokens.items():
            resp = client.put(
                "/api/v1/profiles/me",
                json={"bio": f"{uname} writes python and react"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
        headers = {"Authorization": f"Bearer {tokens['cachec']}"}

        first = client.get("/api/v1/recommendations", headers=headers)
        assert first.status_code == 200
        assert len(result_cache._store) >= 1

        # Profile write bumps the version → new cache key, same correct data.
        before_keys = set(result_cache._store.keys())
        client.put(
            "/api/v1/profiles/me",
            json={"bio": "cache invalidation check"},
            headers=headers,
        )
        second = client.get("/api/v1/recommendations", headers=headers)
        assert second.status_code == 200
        assert set(result_cache._store.keys()) != before_keys

    def test_request_id_header_present(self, client):
        response = client.get("/health")
        assert "X-Request-ID" in response.headers
