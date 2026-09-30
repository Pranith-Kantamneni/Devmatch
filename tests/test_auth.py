from datetime import datetime, timedelta, timezone

import jwt
from fastapi import status

from app.core.config import get_settings
from conftest import auth_headers, login_user, register_user


class TestRegister:
    def test_register_success(self, client):
        response = register_user(
            client, "alice", "alice@example.com", "password123"
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"
        assert "id" in data
        assert "created_at" in data

    def test_register_does_not_leak_password(self, client):
        response = register_user(
            client, "alice", "alice@example.com", "password123"
        )
        assert "password" not in response.json()
        assert "password_hash" not in response.json()

    def test_register_duplicate_email(self, client):
        register_user(client, "alice", "alice@example.com")
        response = register_user(client, "alice2", "alice@example.com")
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_register_duplicate_username(self, client):
        register_user(client, "alice", "alice@example.com")
        response = register_user(client, "alice", "alice2@example.com")
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_register_invalid_username_too_short(self, client):
        response = register_user(client, "ab", "alice@example.com")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_register_invalid_username_characters(self, client):
        response = register_user(client, "alice!", "alice@example.com")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_register_weak_password(self, client):
        response = register_user(client, "alice", "alice@example.com", "short")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_register_invalid_email(self, client):
        response = register_user(client, "alice", "not-an-email")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_register_missing_fields(self, client):
        response = client.post("/api/v1/auth/register", json={"username": "alice"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestLogin:
    def test_login_success(self, client):
        register_user(client, "alice", "alice@example.com", "password123")
        response = login_user(client, "alice@example.com", "password123")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_password(self, client):
        register_user(client, "alice", "alice@example.com", "password123")
        response = login_user(client, "alice@example.com", "wrongpassword")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client):
        response = login_user(client, "nobody@example.com", "password123")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_invalid_email_format(self, client):
        response = login_user(client, "not-an-email", "password123")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_login_wrong_password_does_not_leak_user(self, client):
        register_user(client, "alice", "alice@example.com", "password123")
        response = login_user(client, "alice@example.com", "wrongpassword")
        assert response.json()["detail"] == "Invalid email or password"


class TestProtectedRoutes:
    def test_protected_route_without_token(self, client):
        response = client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_route_invalid_token(self, client):
        headers = auth_headers("this-is-not-a-valid-token")
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_route_expired_token(self, client):
        settings = get_settings()
        payload = {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        expired_token = jwt.encode(
            payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        headers = auth_headers(expired_token)
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Token has expired"

    def test_protected_route_malformed_token(self, client):
        headers = auth_headers("abc.def.ghi")
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
