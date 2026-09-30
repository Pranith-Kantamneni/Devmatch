from fastapi import status

from conftest import create_user_with_token, register_user


class TestListUsers:
    def test_list_users_empty(self, client):
        response = client.get("/api/v1/users/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_users_returns_public_info(self, client):
        register_user(client, "alice", "alice@example.com")
        response = client.get("/api/v1/users/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["username"] == "alice"
        assert "email" not in data[0]
        assert "password_hash" not in data[0]

    def test_list_users_pagination(self, client):
        for i in range(5):
            register_user(client, f"user{i}", f"user{i}@example.com")
        response = client.get("/api/v1/users/?skip=1&limit=2")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    def test_list_users_limit_validation(self, client):
        response = client.get("/api/v1/users/?limit=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_list_users_skip_validation(self, client):
        response = client.get("/api/v1/users/?skip=-1")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestGetMe:
    def test_get_me_success(self, client):
        register_user(client, "alice", "alice@example.com")
        headers = create_user_with_token(client, "alice", "alice@example.com")
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"

    def test_get_me_requires_auth(self, client):
        response = client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
