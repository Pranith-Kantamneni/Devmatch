from fastapi import status

from conftest import create_user_with_token


class TestUpdateProfile:
    def test_update_profile_creates_profile(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        response = client.put(
            "/api/v1/profiles/me",
            json={"full_name": "Alice Anderson", "bio": "Python developer"},
            headers=headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "Alice Anderson"
        assert data["bio"] == "Python developer"

    def test_update_profile_partial(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        client.put(
            "/api/v1/profiles/me",
            json={"full_name": "Alice Anderson", "bio": "Python developer"},
            headers=headers,
        )
        response = client.put(
            "/api/v1/profiles/me",
            json={"location": "Berlin"},
            headers=headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["location"] == "Berlin"
        assert data["full_name"] == "Alice Anderson"
        assert data["bio"] == "Python developer"

    def test_update_profile_invalid_experience_level(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        response = client.put(
            "/api/v1/profiles/me",
            json={"experience_level": "wizard"},
            headers=headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_update_profile_requires_auth(self, client):
        response = client.put("/api/v1/profiles/me", json={"full_name": "Alice"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetOwnProfile:
    def test_get_own_profile(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        client.put(
            "/api/v1/profiles/me",
            json={"full_name": "Alice Anderson", "experience_level": "senior"},
            headers=headers,
        )
        response = client.get("/api/v1/profiles/me", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "Alice Anderson"
        assert data["experience_level"] == "senior"
        assert data["skills"] == []
        assert data["projects"] == []

    def test_get_own_profile_auto_created(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        response = client.get("/api/v1/profiles/me", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["skills"] == []


class TestGetPublicProfile:
    def test_get_public_profile(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        client.put(
            "/api/v1/profiles/me",
            json={"full_name": "Alice Anderson", "bio": "Python developer"},
            headers=headers,
        )
        response = client.get("/api/v1/profiles/1")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "Alice Anderson"
        assert data["user_id"] == 1
        assert "email" not in data

    def test_get_public_profile_not_found(self, client):
        response = client.get("/api/v1/profiles/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSkills:
    def test_add_skill(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        response = client.post(
            "/api/v1/profiles/me/skills",
            json={"name": "Python", "category": "language", "proficiency": 5},
            headers=headers,
        )
        assert response.status_code == status.HTTP_201_CREATED
        skills = response.json()["skills"]
        assert len(skills) == 1
        assert skills[0]["name"] == "python"
        assert skills[0]["proficiency"] == 5

    def test_add_duplicate_skill(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        client.post(
            "/api/v1/profiles/me/skills",
            json={"name": "Python", "category": "language"},
            headers=headers,
        )
        response = client.post(
            "/api/v1/profiles/me/skills",
            json={"name": "Python", "category": "language"},
            headers=headers,
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_add_skill_invalid_proficiency(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        response = client.post(
            "/api/v1/profiles/me/skills",
            json={"name": "Python", "proficiency": 10},
            headers=headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_add_skill_invalid_category(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        response = client.post(
            "/api/v1/profiles/me/skills",
            json={"name": "Python", "category": "invalid"},
            headers=headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_remove_skill(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        client.post(
            "/api/v1/profiles/me/skills",
            json={"name": "Python", "category": "language"},
            headers=headers,
        )
        skill_id = client.get("/api/v1/profiles/me", headers=headers).json()[
            "skills"
        ][0]["skill_id"]
        response = client.delete(
            f"/api/v1/profiles/me/skills/{skill_id}", headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["skills"] == []

    def test_add_skill_requires_auth(self, client):
        response = client.post(
            "/api/v1/profiles/me/skills",
            json={"name": "Python", "category": "language"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestProjects:
    def test_add_project(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        response = client.post(
            "/api/v1/profiles/me/projects",
            json={"title": "ML Pipeline", "description": "A cool project"},
            headers=headers,
        )
        assert response.status_code == status.HTTP_201_CREATED
        projects = response.json()["projects"]
        assert len(projects) == 1
        assert projects[0]["title"] == "ML Pipeline"

    def test_add_project_with_skills(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        response = client.post(
            "/api/v1/profiles/me/projects",
            json={
                "title": "ML Pipeline",
                "skill_names": ["Python", "Machine Learning"],
            },
            headers=headers,
        )
        assert response.status_code == status.HTTP_201_CREATED
        skills = response.json()["projects"][0]["skills"]
        skill_names = {s["name"] for s in skills}
        assert skill_names == {"python", "machine learning"}

    def test_add_project_empty_title(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        response = client.post(
            "/api/v1/profiles/me/projects",
            json={"title": ""},
            headers=headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_remove_project(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        client.post(
            "/api/v1/profiles/me/projects",
            json={"title": "ML Pipeline"},
            headers=headers,
        )
        project_id = client.get("/api/v1/profiles/me", headers=headers).json()[
            "projects"
        ][0]["id"]
        response = client.delete(
            f"/api/v1/profiles/me/projects/{project_id}", headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["projects"] == []

    def test_add_project_requires_auth(self, client):
        response = client.post(
            "/api/v1/profiles/me/projects", json={"title": "ML Pipeline"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
