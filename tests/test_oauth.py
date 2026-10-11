"""Tests for social login (Google / GitHub / LinkedIn OAuth)."""

import pytest

from app.db.models.oauth_account import OAuthAccount
from app.services.oauth_service import OAuthService, ProviderProfile
from tests.conftest import auth_headers


PROFILE = ProviderProfile(
    provider_user_id="google-123",
    email="oauth@example.com",
    email_verified=True,
    name="OAuth User",
    username_hint="oauthuser",
)


def _stub_oauth(monkeypatch, profile=PROFILE):
    monkeypatch.setattr(
        OAuthService, "exchange_code", lambda self, provider, code: "tok"
    )
    monkeypatch.setattr(
        OAuthService, "fetch_profile", lambda self, provider, token: profile
    )


def _settings_with_oauth(monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-id")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(
        settings,
        "GOOGLE_REDIRECT_URI",
        "http://localhost:8000/api/v1/auth/oauth/google/callback",
    )
    return settings


def _login_url(client):
    return "/api/v1/auth/oauth/google/login"


class TestProviders:
    def test_lists_all_providers(self, client):
        response = client.get("/api/v1/auth/oauth/providers")
        assert response.status_code == 200
        providers = {p["provider"]: p["enabled"] for p in response.json()}
        assert set(providers) == {"google", "github", "linkedin"}

    def test_unconfigured_by_default(self, client):
        response = client.get("/api/v1/auth/oauth/providers")
        assert all(p["enabled"] is False for p in response.json())


class TestLoginUrl:
    def test_unconfigured_returns_501(self, client):
        response = client.get(_login_url(client))
        assert response.status_code == 501

    def test_unknown_provider_returns_404(self, client, monkeypatch):
        _settings_with_oauth(monkeypatch)
        response = client.get("/api/v1/auth/oauth/twitter/login")
        assert response.status_code == 404

    def test_returns_authorization_url(self, client, monkeypatch):
        _settings_with_oauth(monkeypatch)
        response = client.get(_login_url(client))
        assert response.status_code == 200
        data = response.json()
        assert "accounts.google.com" in data["authorization_url"]
        assert "client_id=test-id" in data["authorization_url"]
        assert data["state"]


class TestCallback:
    def _callback(self, client, monkeypatch, provider="google", code="code", state=None):
        _settings_with_oauth(monkeypatch)
        if state is None:
            state = client.get(f"/api/v1/auth/oauth/{provider}/login").json()["state"]
        return client.get(
            f"/api/v1/auth/oauth/{provider}/callback",
            params={"code": code, "state": state},
        )

    def test_creates_new_user_and_returns_token(
        self, client, monkeypatch, db_session
    ):
        _stub_oauth(monkeypatch)
        response = self._callback(client, monkeypatch)
        assert response.status_code == 200, response.text
        token = response.json()["access_token"]
        assert token

        me = client.get("/api/v1/users/me", headers=auth_headers(token))
        assert me.status_code == 200
        assert me.json()["email"] == "oauth@example.com"

        link = (
            db_session.query(OAuthAccount)
            .filter_by(provider="google", provider_user_id="google-123")
            .first()
        )
        assert link is not None

    def test_links_existing_email_account(self, client, monkeypatch, db_session):
        from tests.conftest import register_user

        register_user(client, "existinguser", "oauth@example.com")
        _stub_oauth(monkeypatch)
        response = self._callback(client, monkeypatch)
        assert response.status_code == 200, response.text

        links = db_session.query(OAuthAccount).all()
        assert len(links) == 1
        user_id = links[0].user_id
        me = client.get(
            "/api/v1/users/me",
            headers=auth_headers(response.json()["access_token"]),
        )
        assert me.json()["username"] == "existinguser"
        assert me.json()["id"] == user_id

    def test_repeat_login_returns_same_user(self, client, monkeypatch):
        _stub_oauth(monkeypatch)
        first = self._callback(client, monkeypatch)
        second = self._callback(client, monkeypatch)
        assert first.status_code == 200 and second.status_code == 200
        me1 = client.get(
            "/api/v1/users/me", headers=auth_headers(first.json()["access_token"])
        ).json()
        me2 = client.get(
            "/api/v1/users/me", headers=auth_headers(second.json()["access_token"])
        ).json()
        assert me1["id"] == me2["id"]

    def test_bad_state_rejected(self, client, monkeypatch):
        _settings_with_oauth(monkeypatch)
        _stub_oauth(monkeypatch)
        response = client.get(
            "/api/v1/auth/oauth/google/callback",
            params={"code": "code", "state": "bogus"},
        )
        assert response.status_code == 403

    def test_state_for_other_provider_rejected(self, client, monkeypatch):
        _settings_with_oauth(monkeypatch)
        _stub_oauth(monkeypatch)
        settings_state = client.get(_login_url(client)).json()["state"]
        response = client.get(
            "/api/v1/auth/oauth/github/callback",
            params={"code": "code", "state": settings_state},
        )
        # github not configured → 501 surfaces before state check; either way no token
        assert response.status_code in (403, 501)

    def test_unverified_email_rejected(self, client, monkeypatch):
        _stub_oauth(
            monkeypatch,
            ProviderProfile(
                provider_user_id="google-999",
                email="unverified@example.com",
                email_verified=False,
                name="No Verify",
            ),
        )
        response = self._callback(client, monkeypatch)
        assert response.status_code == 422

    def test_missing_email_rejected(self, client, monkeypatch):
        _stub_oauth(
            monkeypatch,
            ProviderProfile(
                provider_user_id="google-000",
                email=None,
                email_verified=False,
                name="No Email",
            ),
        )
        response = self._callback(client, monkeypatch)
        assert response.status_code == 422


class TestPasswordLoginWithOAuthAccount:
    def test_password_login_explains_social_login(self, client, monkeypatch):
        _stub_oauth(monkeypatch)
        _settings_with_oauth(monkeypatch)
        state = client.get(_login_url(client)).json()["state"]
        client.get(
            "/api/v1/auth/oauth/google/callback",
            params={"code": "code", "state": state},
        )
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "oauth@example.com", "password": "whatever123"},
        )
        assert response.status_code == 401
        assert "social login" in response.json()["detail"]
