from fastapi import status

from conftest import create_user_with_token, login_user


def make_headers(client, username, email):
    return create_user_with_token(client, username, email)


def make_team(client, headers, **kwargs):
    payload = {"title": "Filter Team", "max_members": 4}
    payload.update(kwargs)
    return client.post("/api/v1/team-projects", json=payload, headers=headers)


class TestIdentifierLogin:
    def test_login_with_username(self, client):
        make_headers(client, "idlogin", "idlogin@example.com")
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "idlogin", "password": "password123"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["access_token"]

    def test_login_with_email_still_works(self, client):
        make_headers(client, "idlogin2", "idlogin2@example.com")
        response = login_user(client, "idlogin2@example.com")
        assert response.status_code == status.HTTP_200_OK


class TestRefreshTokens:
    def test_login_returns_pair_and_refresh_rotates(self, client):
        make_headers(client, "ref_alice", "ref_alice@example.com")
        pair = login_user(client, "ref_alice@example.com").json()
        assert pair["refresh_token"]

        rotated = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]}
        )
        assert rotated.status_code == status.HTTP_200_OK
        fresh = rotated.json()
        assert fresh["access_token"]
        assert fresh["refresh_token"] != pair["refresh_token"]

        # Old refresh token is dead.
        replay = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]}
        )
        assert replay.status_code == status.HTTP_401_UNAUTHORIZED
        # New access token works.
        me = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {fresh['access_token']}"},
        )
        assert me.status_code == status.HTTP_200_OK

    def test_logout_revokes(self, client):
        make_headers(client, "ref_bob", "ref_bob@example.com")
        pair = login_user(client, "ref_bob@example.com").json()
        out = client.post(
            "/api/v1/auth/logout", json={"refresh_token": pair["refresh_token"]}
        )
        assert out.status_code == status.HTTP_204_NO_CONTENT
        gone = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]}
        )
        assert gone.status_code == status.HTTP_401_UNAUTHORIZED

    def test_bogus_refresh_rejected(self, client):
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMultiChoicePolls:
    def _team_with_member(self, client):
        h1 = make_headers(client, "poll_m1", "poll_m1@example.com")
        h2 = make_headers(client, "poll_m2", "poll_m2@example.com")
        project_id = make_team(client, h1).json()["id"]
        client.post(
            f"/api/v1/team-projects/{project_id}/apply", json={}, headers=h2
        )
        app_id = client.get(
            f"/api/v1/team-projects/{project_id}/applications", headers=h1
        ).json()[0]["id"]
        client.post(
            f"/api/v1/team-projects/{project_id}/applications/{app_id}/accept",
            headers=h1,
        )
        return h1, h2, project_id

    def test_multi_select_toggle(self, client):
        h1, h2, project_id = self._team_with_member(client)
        poll = client.post(
            f"/api/v1/team-projects/{project_id}/polls",
            json={
                "question": "Pick stack",
                "options": ["React", "Vue", "Svelte"],
                "allow_multiple": True,
            },
            headers=h1,
        ).json()
        assert poll["allow_multiple"] is True
        by_text = {o["text"]: o["id"] for o in poll["options"]}
        client.post(
            f"/api/v1/team-projects/{project_id}/polls/{poll['id']}/vote",
            json={"option_id": by_text["React"]},
            headers=h2,
        )
        client.post(
            f"/api/v1/team-projects/{project_id}/polls/{poll['id']}/vote",
            json={"option_id": by_text["Vue"]},
            headers=h2,
        )
        listed = client.get(
            f"/api/v1/team-projects/{project_id}/polls", headers=h2
        ).json()[0]
        assert sorted(listed["my_option_ids"]) == sorted(
            [by_text["React"], by_text["Vue"]]
        )
        assert listed["total_votes"] == 2
        # Toggling React off removes just that vote.
        client.post(
            f"/api/v1/team-projects/{project_id}/polls/{poll['id']}/vote",
            json={"option_id": by_text["React"]},
            headers=h2,
        )
        listed = client.get(
            f"/api/v1/team-projects/{project_id}/polls", headers=h2
        ).json()[0]
        assert listed["my_option_ids"] == [by_text["Vue"]]

    def test_member_poll_permission(self, client):
        h1, h2, project_id = self._team_with_member(client)
        # Members can create polls by default.
        ok = client.post(
            f"/api/v1/team-projects/{project_id}/polls",
            json={"question": "Q?", "options": ["A", "B"]},
            headers=h2,
        )
        assert ok.status_code == status.HTTP_201_CREATED
        # Creator disables member polls.
        client.put(
            f"/api/v1/team-projects/{project_id}",
            json={"allow_member_polls": False},
            headers=h1,
        )
        denied = client.post(
            f"/api/v1/team-projects/{project_id}/polls",
            json={"question": "Q2?", "options": ["A", "B"]},
            headers=h2,
        )
        assert denied.status_code == status.HTTP_403_FORBIDDEN

    def test_member_invite_permission(self, client):
        h1, h2, project_id = self._team_with_member(client)
        h3 = make_headers(client, "poll_m3", "poll_m3@example.com")
        target = client.get("/api/v1/users/me", headers=h3).json()["id"]
        denied = client.post(
            f"/api/v1/team-projects/{project_id}/invite",
            json={"user_id": target},
            headers=h2,
        )
        assert denied.status_code == status.HTTP_403_FORBIDDEN
        client.put(
            f"/api/v1/team-projects/{project_id}",
            json={"allow_member_invites": True},
            headers=h1,
        )
        allowed = client.post(
            f"/api/v1/team-projects/{project_id}/invite",
            json={"user_id": target},
            headers=h2,
        )
        assert allowed.status_code == status.HTTP_201_CREATED

    def test_system_message_on_join(self, client):
        h1, h2, project_id = self._team_with_member(client)
        messages = client.get(
            f"/api/v1/team-projects/{project_id}/messages", headers=h1
        ).json()
        assert any(
            m["sender_username"] == "DevMatch" and "joined" in m["body"]
            for m in messages
        )


class TestDiscovery:
    def _seed(self, client):
        h1 = make_headers(client, "disc_alice", "disc_alice@example.com")
        client.put(
            "/api/v1/profiles/me",
            json={"bio": "python dev"},
            headers=h1,
        )
        client.post(
            "/api/v1/profiles/me/skills",
            json={"name": "Python", "category": "language"},
            headers=h1,
        )
        make_team(
            client,
            h1,
            title="AI Hackers",
            kind="hackathon",
            category="AI/ML",
            hackathon_name="HackNight",
            location="Chennai",
            work_mode="remote",
            tech_stack=["Python"],
            required_skills=[{"name": "Python", "category": "language"}],
        )
        make_team(
            client,
            h1,
            title="Web Studio",
            kind="project",
            category="Web Development",
            location="Bangalore",
            work_mode="onsite",
            tech_stack=["React"],
            required_skills=[{"name": "React", "category": "framework"}],
        )
        return h1

    def test_kind_filter(self, client):
        h1 = self._seed(client)
        data = client.get(
            "/api/v1/team-projects", params={"kind": "hackathon"}, headers=h1
        ).json()
        assert [t["title"] for t in data] == ["AI Hackers"]

    def test_category_and_location_filters(self, client):
        h1 = self._seed(client)
        data = client.get(
            "/api/v1/team-projects", params={"category": "AI/ML"}, headers=h1
        ).json()
        assert [t["title"] for t in data] == ["AI Hackers"]
        data = client.get(
            "/api/v1/team-projects", params={"location": "chennai"}, headers=h1
        ).json()
        assert [t["title"] for t in data] == ["AI Hackers"]

    def test_work_mode_and_hackathon_filters(self, client):
        h1 = self._seed(client)
        data = client.get(
            "/api/v1/team-projects", params={"work_mode": "remote"}, headers=h1
        ).json()
        assert [t["title"] for t in data] == ["AI Hackers"]
        data = client.get(
            "/api/v1/team-projects", params={"hackathon": "hacknight"}, headers=h1
        ).json()
        assert [t["title"] for t in data] == ["AI Hackers"]

    def test_match_my_stack_and_sort(self, client):
        h1 = self._seed(client)
        data = client.get(
            "/api/v1/team-projects",
            params={"match_my_stack": "true", "sort": "tech_match"},
            headers=h1,
        ).json()
        assert [t["title"] for t in data] == ["AI Hackers"]
        assert data[0]["match_coverage"] == 1.0

    def test_tech_filter_multi(self, client):
        h1 = self._seed(client)
        data = client.get(
            "/api/v1/team-projects",
            params=[("tech", "React"), ("tech", "Go")],
            headers=h1,
        ).json()
        assert [t["title"] for t in data] == ["Web Studio"]

    def test_open_only(self, client):
        h1 = self._seed(client)
        h2 = make_headers(client, "disc_bob", "disc_bob@example.com")
        h3 = make_headers(client, "disc_cid", "disc_cid@example.com")
        h4 = make_headers(client, "disc_dan", "disc_dan@example.com")
        full = make_team(client, h1, title="Full House", max_members=2).json()
        for h in (h2,):
            client.post(
                f"/api/v1/team-projects/{full['id']}/apply", json={}, headers=h
            )
        app_id = client.get(
            f"/api/v1/team-projects/{full['id']}/applications", headers=h1
        ).json()[0]["id"]
        client.post(
            f"/api/v1/team-projects/{full['id']}/applications/{app_id}/accept",
            headers=h1,
        )
        data = client.get(
            "/api/v1/team-projects", params={"open_only": "true"}, headers=h3
        ).json()
        titles = [t["title"] for t in data]
        assert "Full House" not in titles
        assert "AI Hackers" in titles

    def test_my_teams_split(self, client):
        h1 = make_headers(client, "split_alice", "split_alice@example.com")
        h2 = make_headers(client, "split_bob", "split_bob@example.com")
        make_team(client, h1, title="Alice Owns")
        pid = make_team(client, h2, title="Bob Owns").json()["id"]
        client.post(
            f"/api/v1/team-projects/{pid}/apply", json={}, headers=h1
        )
        app_id = client.get(
            f"/api/v1/team-projects/{pid}/applications", headers=h2
        ).json()[0]["id"]
        client.post(
            f"/api/v1/team-projects/{pid}/applications/{app_id}/accept", headers=h2
        )
        joined = client.get("/api/v1/team-projects/me/teams", headers=h1).json()
        assert [t["title"] for t in joined] == ["Bob Owns"]


class TestTeammateSearch:
    def test_search_by_skill(self, client):
        from test_team_projects import make_user

        make_user(client, "sea_alice", "sea_alice@example.com", ["Python"])
        make_user(client, "sea_bob", "sea_bob@example.com", ["Python", "Docker"])
        make_user(client, "sea_cid", "sea_cid@example.com", ["Java"])
        headers = make_headers(client, "sea_dan", "sea_dan@example.com")
        client.put("/api/v1/profiles/me", json={"bio": "x"}, headers=headers)
        data = client.get(
            "/api/v1/recommendations", params={"q": "docker", "limit": 10}, headers=headers
        ).json()
        assert [r["user"]["username"] for r in data["recommendations"]] == ["sea_bob"]
        data = client.get(
            "/api/v1/recommendations", params={"q": "sea_", "limit": 10}, headers=headers
        ).json()
        assert len(data["recommendations"]) == 3
