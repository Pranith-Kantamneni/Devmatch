from fastapi import status

from conftest import create_user_with_token


def make_user(client, username, email, skills=None, college=None, level="senior"):
    headers = create_user_with_token(client, username, email)
    payload = {"full_name": username, "bio": "developer", "experience_level": level}
    if college:
        payload["college"] = college
    client.put("/api/v1/profiles/me", json=payload, headers=headers)
    for skill in skills or []:
        client.post(
            "/api/v1/profiles/me/skills",
            json={"name": skill, "category": "language", "proficiency": 4},
            headers=headers,
        )
    return headers


def make_project(client, headers, **kwargs):
    payload = {
        "title": "AI Hackathon",
        "description": "Build an AI app",
        "tech_stack": ["Python", "React"],
        "required_skills": [{"name": "Python", "category": "language"}],
        "max_members": 4,
    }
    payload.update(kwargs)
    return client.post("/api/v1/team-projects", json=payload, headers=headers)


class TestCreateProject:
    def test_create_success(self, client):
        headers = make_user(client, "alice", "alice@example.com", ["Python"])
        response = make_project(client, headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "AI Hackathon"
        assert data["member_count"] == 1
        assert data["tech_stack"] == ["Python", "React"]
        assert len(data["required_skills"]) == 1

    def test_create_requires_auth(self, client):
        response = client.post("/api/v1/team-projects", json={"title": "X", "max_members": 4})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_invalid_max_members(self, client):
        headers = make_user(client, "alice", "alice@example.com")
        response = make_project(client, headers, max_members=1)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_same_college_requires_college(self, client):
        headers = make_user(client, "alice", "alice@example.com")
        response = make_project(client, headers, require_same_college=True)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_same_college_with_college(self, client):
        headers = make_user(client, "alice", "alice@example.com")
        response = make_project(
            client, headers, college="MIT", require_same_college=True
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["require_same_college"] is True


class TestDiscoverProjects:
    def test_list_projects(self, client):
        headers = make_user(client, "alice", "alice@example.com")
        make_project(client, headers, title="Project A")
        make_project(client, headers, title="Project B")
        response = client.get("/api/v1/team-projects")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 2

    def test_list_filter_college(self, client):
        headers = make_user(client, "alice", "alice@example.com")
        make_project(client, headers, title="MIT Project", college="MIT")
        make_project(client, headers, title="Other Project", college="Stanford")
        response = client.get("/api/v1/team-projects?college=MIT")
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "MIT Project"

    def test_list_search(self, client):
        headers = make_user(client, "alice", "alice@example.com")
        make_project(client, headers, title="AI Hackathon")
        make_project(client, headers, title="Web App")
        response = client.get("/api/v1/team-projects?q=hackathon")
        assert len(response.json()) == 1


class TestProjectDetail:
    def test_detail_public(self, client):
        headers = make_user(client, "alice", "alice@example.com")
        project_id = make_project(client, headers).json()["id"]
        response = client.get(f"/api/v1/team-projects/{project_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["members"]) == 1
        assert data["members"][0]["role"] == "creator"

    def test_detail_viewer_flags_creator(self, client):
        headers = make_user(client, "alice", "alice@example.com")
        project_id = make_project(client, headers).json()["id"]
        data = client.get(f"/api/v1/team-projects/{project_id}", headers=headers).json()
        assert data["is_creator"] is True
        assert data["is_member"] is True

    def test_detail_viewer_flags_outsider(self, client):
        h1 = make_user(client, "alice", "alice@example.com")
        h2 = make_user(client, "bob", "bob@example.com")
        project_id = make_project(client, h1).json()["id"]
        data = client.get(f"/api/v1/team-projects/{project_id}", headers=h2).json()
        assert data["is_creator"] is False
        assert data["is_member"] is False
        assert data["application_status"] is None

    def test_detail_not_found(self, client):
        response = client.get("/api/v1/team-projects/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateDelete:
    def test_update_by_creator(self, client):
        headers = make_user(client, "alice", "alice@example.com")
        project_id = make_project(client, headers).json()["id"]
        response = client.put(
            f"/api/v1/team-projects/{project_id}",
            json={"title": "New Title", "max_members": 5},
            headers=headers,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["title"] == "New Title"

    def test_update_forbidden(self, client):
        h1 = make_user(client, "alice", "alice@example.com")
        h2 = make_user(client, "bob", "bob@example.com")
        project_id = make_project(client, h1).json()["id"]
        response = client.put(
            f"/api/v1/team-projects/{project_id}", json={"title": "Hijack"}, headers=h2
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_max_members_below_current(self, client):
        h1 = make_user(client, "alice", "alice@example.com")
        h2 = make_user(client, "bob", "bob@example.com", ["Python"])
        project_id = make_project(client, h1, max_members=4).json()["id"]
        client.post(f"/api/v1/team-projects/{project_id}/apply", json={}, headers=h2)
        app_id = client.get(
            f"/api/v1/team-projects/{project_id}/applications", headers=h1
        ).json()[0]["id"]
        client.post(
            f"/api/v1/team-projects/{project_id}/applications/{app_id}/accept",
            headers=h1,
        )
        response = client.put(
            f"/api/v1/team-projects/{project_id}", json={"max_members": 1}, headers=h1
        )
        assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_CONTENT)

    def test_delete_by_creator(self, client):
        headers = make_user(client, "alice", "alice@example.com")
        project_id = make_project(client, headers).json()["id"]
        response = client.delete(f"/api/v1/team-projects/{project_id}", headers=headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert client.get(f"/api/v1/team-projects/{project_id}").status_code == 404

    def test_delete_forbidden(self, client):
        h1 = make_user(client, "alice", "alice@example.com")
        h2 = make_user(client, "bob", "bob@example.com")
        project_id = make_project(client, h1).json()["id"]
        response = client.delete(f"/api/v1/team-projects/{project_id}", headers=h2)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestRequiredSkills:
    def test_add_required_skill(self, client):
        headers = make_user(client, "alice", "alice@example.com")
        project_id = make_project(client, headers).json()["id"]
        response = client.post(
            f"/api/v1/team-projects/{project_id}/skills",
            json={"name": "React", "category": "framework"},
            headers=headers,
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.json()["required_skills"]) == 2

    def test_add_duplicate_skill(self, client):
        headers = make_user(client, "alice", "alice@example.com")
        project_id = make_project(client, headers).json()["id"]
        response = client.post(
            f"/api/v1/team-projects/{project_id}/skills",
            json={"name": "Python", "category": "language"},
            headers=headers,
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_add_skill_forbidden(self, client):
        h1 = make_user(client, "alice", "alice@example.com")
        h2 = make_user(client, "bob", "bob@example.com")
        project_id = make_project(client, h1).json()["id"]
        response = client.post(
            f"/api/v1/team-projects/{project_id}/skills",
            json={"name": "React", "category": "framework"},
            headers=h2,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestApplications:
    def test_apply_success(self, client):
        h1 = make_user(client, "alice", "alice@example.com")
        h2 = make_user(client, "bob", "bob@example.com", ["Python"])
        project_id = make_project(client, h1).json()["id"]
        response = client.post(
            f"/api/v1/team-projects/{project_id}/apply",
            json={"message": "I want to join"},
            headers=h2,
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["status"] == "pending"

    def test_apply_duplicate(self, client):
        h1 = make_user(client, "alice", "alice@example.com")
        h2 = make_user(client, "bob", "bob@example.com")
        project_id = make_project(client, h1).json()["id"]
        client.post(f"/api/v1/team-projects/{project_id}/apply", json={}, headers=h2)
        response = client.post(
            f"/api/v1/team-projects/{project_id}/apply", json={}, headers=h2
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_creator_cannot_apply(self, client):
        headers = make_user(client, "alice", "alice@example.com")
        project_id = make_project(client, headers).json()["id"]
        response = client.post(
            f"/api/v1/team-projects/{project_id}/apply", json={}, headers=headers
        )
        assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_CONTENT)

    def test_apply_full_team(self, client):
        h1 = make_user(client, "alice", "alice@example.com")
        h2 = make_user(client, "bob", "bob@example.com")
        h3 = make_user(client, "carol", "carol@example.com")
        project_id = make_project(client, h1, max_members=2).json()["id"]
        client.post(f"/api/v1/team-projects/{project_id}/apply", json={}, headers=h2)
        app_id = client.get(
            f"/api/v1/team-projects/{project_id}/applications", headers=h1
        ).json()[0]["id"]
        client.post(
            f"/api/v1/team-projects/{project_id}/applications/{app_id}/accept",
            headers=h1,
        )
        response = client.post(
            f"/api/v1/team-projects/{project_id}/apply", json={}, headers=h3
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_apply_college_mismatch(self, client):
        h1 = make_user(client, "alice", "alice@example.com", college="MIT")
        h2 = make_user(client, "bob", "bob@example.com", college="Stanford")
        project_id = make_project(
            client, h1, college="MIT", require_same_college=True
        ).json()["id"]
        response = client.post(
            f"/api/v1/team-projects/{project_id}/apply", json={}, headers=h2
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_apply_college_match(self, client):
        h1 = make_user(client, "alice", "alice@example.com", college="MIT")
        h2 = make_user(client, "bob", "bob@example.com", college="mit")
        project_id = make_project(
            client, h1, college="MIT", require_same_college=True
        ).json()["id"]
        response = client.post(
            f"/api/v1/team-projects/{project_id}/apply", json={}, headers=h2
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_reapply_after_reject(self, client):
        h1 = make_user(client, "alice", "alice@example.com")
        h2 = make_user(client, "bob", "bob@example.com")
        project_id = make_project(client, h1).json()["id"]
        client.post(f"/api/v1/team-projects/{project_id}/apply", json={}, headers=h2)
        app_id = client.get(
            f"/api/v1/team-projects/{project_id}/applications", headers=h1
        ).json()[0]["id"]
        client.post(
            f"/api/v1/team-projects/{project_id}/applications/{app_id}/reject",
            headers=h1,
        )
        response = client.post(
            f"/api/v1/team-projects/{project_id}/apply",
            json={"message": "Second try"},
            headers=h2,
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["status"] == "pending"

    def test_accept_application(self, client):
        h1 = make_user(client, "alice", "alice@example.com")
        h2 = make_user(client, "bob", "bob@example.com")
        project_id = make_project(client, h1).json()["id"]
        client.post(f"/api/v1/team-projects/{project_id}/apply", json={}, headers=h2)
        app_id = client.get(
            f"/api/v1/team-projects/{project_id}/applications", headers=h1
        ).json()[0]["id"]
        response = client.post(
            f"/api/v1/team-projects/{project_id}/applications/{app_id}/accept",
            headers=h1,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "accepted"
        detail = client.get(
            f"/api/v1/team-projects/{project_id}", headers=h2
        ).json()
        assert detail["is_member"] is True
        assert detail["member_count"] == 2

    def test_accept_application_forbidden(self, client):
        h1 = make_user(client, "alice", "alice@example.com")
        h2 = make_user(client, "bob", "bob@example.com")
        h3 = make_user(client, "carol", "carol@example.com")
        project_id = make_project(client, h1).json()["id"]
        client.post(f"/api/v1/team-projects/{project_id}/apply", json={}, headers=h2)
        app_id = client.get(
            f"/api/v1/team-projects/{project_id}/applications", headers=h1
        ).json()[0]["id"]
        response = client.post(
            f"/api/v1/team-projects/{project_id}/applications/{app_id}/accept",
            headers=h3,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_applications_creator_only(self, client):
        h1 = make_user(client, "alice", "alice@example.com")
        h2 = make_user(client, "bob", "bob@example.com")
        project_id = make_project(client, h1).json()["id"]
        response = client.get(
            f"/api/v1/team-projects/{project_id}/applications", headers=h2
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestInvitations:
    def test_invite_success(self, client):
        h1 = make_user(client, "alice", "alice@example.com", ["Python"])
        h2 = make_user(client, "bob", "bob@example.com", ["Python"])
        project_id = make_project(client, h1).json()["id"]
        bob_id = client.get("/api/v1/users/me", headers=h2).json()["id"]
        response = client.post(
            f"/api/v1/team-projects/{project_id}/invite",
            json={"user_id": bob_id},
            headers=h1,
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["status"] == "pending"

    def test_invite_duplicate(self, client):
        h1 = make_user(client, "alice", "alice@example.com")
        h2 = make_user(client, "bob", "bob@example.com")
        project_id = make_project(client, h1).json()["id"]
        bob_id = client.get("/api/v1/users/me", headers=h2).json()["id"]
        client.post(
            f"/api/v1/team-projects/{project_id}/invite",
            json={"user_id": bob_id},
            headers=h1,
        )
        response = client.post(
            f"/api/v1/team-projects/{project_id}/invite",
            json={"user_id": bob_id},
            headers=h1,
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_invite_nonexistent_user(self, client):
        headers = make_user(client, "alice", "alice@example.com")
        project_id = make_project(client, headers).json()["id"]
        response = client.post(
            f"/api/v1/team-projects/{project_id}/invite",
            json={"user_id": 999},
            headers=headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_invite_college_mismatch(self, client):
        h1 = make_user(client, "alice", "alice@example.com", college="MIT")
        h2 = make_user(client, "bob", "bob@example.com", college="Stanford")
        project_id = make_project(
            client, h1, college="MIT", require_same_college=True
        ).json()["id"]
        bob_id = client.get("/api/v1/users/me", headers=h2).json()["id"]
        response = client.post(
            f"/api/v1/team-projects/{project_id}/invite",
            json={"user_id": bob_id},
            headers=h1,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_accept_invitation(self, client):
        h1 = make_user(client, "alice", "alice@example.com")
        h2 = make_user(client, "bob", "bob@example.com")
        project_id = make_project(client, h1).json()["id"]
        bob_id = client.get("/api/v1/users/me", headers=h2).json()["id"]
        client.post(
            f"/api/v1/team-projects/{project_id}/invite",
            json={"user_id": bob_id},
            headers=h1,
        )
        inv_id = client.get("/api/v1/team-projects/me/invitations", headers=h2).json()[0]["id"]
        response = client.post(
            f"/api/v1/team-projects/invitations/{inv_id}/accept", headers=h2
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "accepted"
        detail = client.get(
            f"/api/v1/team-projects/{project_id}", headers=h2
        ).json()
        assert detail["is_member"] is True

    def test_accept_invitation_forbidden(self, client):
        h1 = make_user(client, "alice", "alice@example.com")
        h2 = make_user(client, "bob", "bob@example.com")
        h3 = make_user(client, "carol", "carol@example.com")
        project_id = make_project(client, h1).json()["id"]
        bob_id = client.get("/api/v1/users/me", headers=h2).json()["id"]
        client.post(
            f"/api/v1/team-projects/{project_id}/invite",
            json={"user_id": bob_id},
            headers=h1,
        )
        inv_id = client.get("/api/v1/team-projects/me/invitations", headers=h2).json()[0]["id"]
        response = client.post(
            f"/api/v1/team-projects/invitations/{inv_id}/accept", headers=h3
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_reject_invitation(self, client):
        h1 = make_user(client, "alice", "alice@example.com")
        h2 = make_user(client, "bob", "bob@example.com")
        project_id = make_project(client, h1).json()["id"]
        bob_id = client.get("/api/v1/users/me", headers=h2).json()["id"]
        client.post(
            f"/api/v1/team-projects/{project_id}/invite",
            json={"user_id": bob_id},
            headers=h1,
        )
        inv_id = client.get("/api/v1/team-projects/me/invitations", headers=h2).json()[0]["id"]
        response = client.post(
            f"/api/v1/team-projects/invitations/{inv_id}/reject", headers=h2
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "rejected"


class TestMembers:
    def test_creator_cannot_leave(self, client):
        headers = make_user(client, "alice", "alice@example.com")
        project_id = make_project(client, headers).json()["id"]
        alice_id = client.get("/api/v1/users/me", headers=headers).json()["id"]
        response = client.delete(
            f"/api/v1/team-projects/{project_id}/members/{alice_id}", headers=headers
        )
        assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_CONTENT)

    def test_member_can_leave(self, client):
        h1 = make_user(client, "alice", "alice@example.com")
        h2 = make_user(client, "bob", "bob@example.com")
        project_id = make_project(client, h1).json()["id"]
        client.post(f"/api/v1/team-projects/{project_id}/apply", json={}, headers=h2)
        app_id = client.get(
            f"/api/v1/team-projects/{project_id}/applications", headers=h1
        ).json()[0]["id"]
        client.post(
            f"/api/v1/team-projects/{project_id}/applications/{app_id}/accept",
            headers=h1,
        )
        bob_id = client.get("/api/v1/users/me", headers=h2).json()["id"]
        response = client.delete(
            f"/api/v1/team-projects/{project_id}/members/{bob_id}", headers=h2
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_creator_can_remove_member(self, client):
        h1 = make_user(client, "alice", "alice@example.com")
        h2 = make_user(client, "bob", "bob@example.com")
        project_id = make_project(client, h1).json()["id"]
        client.post(f"/api/v1/team-projects/{project_id}/apply", json={}, headers=h2)
        app_id = client.get(
            f"/api/v1/team-projects/{project_id}/applications", headers=h1
        ).json()[0]["id"]
        client.post(
            f"/api/v1/team-projects/{project_id}/applications/{app_id}/accept",
            headers=h1,
        )
        bob_id = client.get("/api/v1/users/me", headers=h2).json()["id"]
        response = client.delete(
            f"/api/v1/team-projects/{project_id}/members/{bob_id}", headers=h1
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestProjectRecommendations:
    def test_recommendations_creator_only(self, client):
        h1 = make_user(client, "alice", "alice@example.com", ["Python"])
        h2 = make_user(client, "bob", "bob@example.com", ["Python"])
        project_id = make_project(client, h1).json()["id"]
        response = client.get(
            f"/api/v1/team-projects/{project_id}/recommendations", headers=h2
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_recommendations_ranking(self, client):
        h1 = make_user(client, "alice", "alice@example.com", ["Python"])
        make_user(client, "bob", "bob@example.com", ["Python", "FastAPI"])
        make_user(client, "carol", "carol@example.com", ["Java", "Spring"])
        project_id = make_project(client, h1).json()["id"]
        response = client.get(
            f"/api/v1/team-projects/{project_id}/recommendations", headers=h1
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_candidates"] == 2
        assert data["recommendations"][0]["username"] == "bob"
        assert "python" in data["recommendations"][0]["skill_overlap"]

    def test_recommendations_exclude_members(self, client):
        h1 = make_user(client, "alice", "alice@example.com", ["Python"])
        h2 = make_user(client, "bob", "bob@example.com", ["Python"])
        project_id = make_project(client, h1).json()["id"]
        client.post(f"/api/v1/team-projects/{project_id}/apply", json={}, headers=h2)
        app_id = client.get(
            f"/api/v1/team-projects/{project_id}/applications", headers=h1
        ).json()[0]["id"]
        client.post(
            f"/api/v1/team-projects/{project_id}/applications/{app_id}/accept",
            headers=h1,
        )
        data = client.get(
            f"/api/v1/team-projects/{project_id}/recommendations", headers=h1
        ).json()
        assert data["total_candidates"] == 0

    def test_recommendations_college_filter(self, client):
        h1 = make_user(client, "alice", "alice@example.com", ["Python"], college="MIT")
        make_user(client, "bob", "bob@example.com", ["Python"], college="MIT")
        make_user(client, "carol", "carol@example.com", ["Python"], college="Stanford")
        project_id = make_project(
            client, h1, college="MIT", require_same_college=True
        ).json()["id"]
        data = client.get(
            f"/api/v1/team-projects/{project_id}/recommendations", headers=h1
        ).json()
        assert data["total_candidates"] == 1
        assert data["recommendations"][0]["username"] == "bob"

    def test_recommendations_annotate_status(self, client):
        h1 = make_user(client, "alice", "alice@example.com", ["Python"])
        h2 = make_user(client, "bob", "bob@example.com", ["Python"])
        project_id = make_project(client, h1).json()["id"]
        bob_id = client.get("/api/v1/users/me", headers=h2).json()["id"]
        client.post(
            f"/api/v1/team-projects/{project_id}/invite",
            json={"user_id": bob_id},
            headers=h1,
        )
        data = client.get(
            f"/api/v1/team-projects/{project_id}/recommendations", headers=h1
        ).json()
        assert data["recommendations"][0]["invitation_status"] == "pending"
