from fastapi import status

from conftest import create_user_with_token


def make_headers(client, username, email):
    return create_user_with_token(client, username, email)


def user_id(client, headers):
    return client.get("/api/v1/users/me", headers=headers).json()["id"]


def make_team(client, headers):
    return client.post(
        "/api/v1/team-projects",
        json={"title": "Chat Team", "max_members": 4},
        headers=headers,
    ).json()["id"]


def add_member(client, creator_headers, project_id, member_headers):
    client.post(
        f"/api/v1/team-projects/{project_id}/apply", json={}, headers=member_headers
    )
    app_id = client.get(
        f"/api/v1/team-projects/{project_id}/applications", headers=creator_headers
    ).json()[0]["id"]
    client.post(
        f"/api/v1/team-projects/{project_id}/applications/{app_id}/accept",
        headers=creator_headers,
    )


class TestDirectMessages:
    def test_request_accept_chat_flow(self, client):
        h1 = make_headers(client, "dm_alice", "dm_alice@example.com")
        h2 = make_headers(client, "dm_bob", "dm_bob@example.com")
        bob_id = user_id(client, h2)

        req = client.post("/api/v1/chat/requests", json={"user_id": bob_id}, headers=h1)
        assert req.status_code == status.HTTP_201_CREATED
        assert req.json()["status"] == "pending"

        # Bob sees the incoming request.
        overview = client.get("/api/v1/chat/overview", headers=h2).json()
        assert len(overview["incoming_requests"]) == 1
        assert overview["incoming_requests"][0]["other_user"]["username"] == "dm_alice"
        assert overview["conversations"] == []

        # Messaging before accept is forbidden.
        convo_id = req.json()["id"]
        early = client.post(
            f"/api/v1/chat/conversations/{convo_id}/messages",
            json={"body": "hi"},
            headers=h1,
        )
        assert early.status_code == status.HTTP_403_FORBIDDEN

        # Bob accepts; both can now chat.
        accept = client.post(
            f"/api/v1/chat/requests/{convo_id}/accept", headers=h2
        )
        assert accept.status_code == status.HTTP_200_OK
        assert accept.json()["status"] == "accepted"

        sent = client.post(
            f"/api/v1/chat/conversations/{convo_id}/messages",
            json={"body": "Hey Bob!"},
            headers=h1,
        )
        assert sent.status_code == status.HTTP_201_CREATED
        thread = client.get(
            f"/api/v1/chat/conversations/{convo_id}/messages", headers=h2
        ).json()
        assert [m["body"] for m in thread] == ["Hey Bob!"]

        status_check = client.get(
            f"/api/v1/chat/with/{bob_id}", headers=h1
        ).json()
        assert status_check["status"] == "accepted"
        assert status_check["conversation_id"] == convo_id

    def test_self_request_rejected(self, client):
        h1 = make_headers(client, "dm_self", "dm_self@example.com")
        me = user_id(client, h1)
        response = client.post(
            "/api/v1/chat/requests", json={"user_id": me}, headers=h1
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_duplicate_request_rejected(self, client):
        h1 = make_headers(client, "dm_dup1", "dm_dup1@example.com")
        h2 = make_headers(client, "dm_dup2", "dm_dup2@example.com")
        bob_id = user_id(client, h2)
        client.post("/api/v1/chat/requests", json={"user_id": bob_id}, headers=h1)
        again = client.post(
            "/api/v1/chat/requests", json={"user_id": bob_id}, headers=h1
        )
        assert again.status_code == status.HTTP_409_CONFLICT

    def test_outsider_cannot_read_thread(self, client):
        h1 = make_headers(client, "dm_out1", "dm_out1@example.com")
        h2 = make_headers(client, "dm_out2", "dm_out2@example.com")
        h3 = make_headers(client, "dm_out3", "dm_out3@example.com")
        bob_id = user_id(client, h2)
        convo_id = client.post(
            "/api/v1/chat/requests", json={"user_id": bob_id}, headers=h1
        ).json()["id"]
        client.post(f"/api/v1/chat/requests/{convo_id}/accept", headers=h2)
        assert (
            client.get(
                f"/api/v1/chat/conversations/{convo_id}/messages", headers=h3
            ).status_code
            == status.HTTP_403_FORBIDDEN
        )

    def test_reject_then_re_request(self, client):
        h1 = make_headers(client, "dm_rej1", "dm_rej1@example.com")
        h2 = make_headers(client, "dm_rej2", "dm_rej2@example.com")
        bob_id = user_id(client, h2)
        convo_id = client.post(
            "/api/v1/chat/requests", json={"user_id": bob_id}, headers=h1
        ).json()["id"]
        client.post(f"/api/v1/chat/requests/{convo_id}/reject", headers=h2)
        retry = client.post(
            "/api/v1/chat/requests", json={"user_id": bob_id}, headers=h1
        )
        assert retry.status_code == status.HTTP_201_CREATED
        assert retry.json()["status"] == "pending"
        assert retry.json()["id"] == convo_id


class TestTeamChatGate:
    def test_solo_creator_locked_out(self, client):
        h1 = make_headers(client, "gate_alice", "gate_alice@example.com")
        project_id = make_team(client, h1)
        assert (
            client.get(
                f"/api/v1/team-projects/{project_id}/messages", headers=h1
            ).status_code
            == status.HTTP_403_FORBIDDEN
        )
        assert (
            client.get(
                f"/api/v1/team-projects/{project_id}/polls", headers=h1
            ).status_code
            == status.HTTP_403_FORBIDDEN
        )

    def test_unlocks_with_second_member(self, client):
        h1 = make_headers(client, "gate2_alice", "gate2_alice@example.com")
        h2 = make_headers(client, "gate2_bob", "gate2_bob@example.com")
        project_id = make_team(client, h1)
        add_member(client, h1, project_id, h2)
        sent = client.post(
            f"/api/v1/team-projects/{project_id}/messages",
            json={"body": "unlocked!"},
            headers=h1,
        )
        assert sent.status_code == status.HTTP_201_CREATED


class TestPolls:
    def _two_member_team(self, client):
        h1 = make_headers(client, "poll_alice", "poll_alice@example.com")
        h2 = make_headers(client, "poll_bob", "poll_bob@example.com")
        project_id = make_team(client, h1)
        add_member(client, h1, project_id, h2)
        return h1, h2, project_id

    def test_poll_lifecycle(self, client):
        h1, h2, project_id = self._two_member_team(client)
        created = client.post(
            f"/api/v1/team-projects/{project_id}/polls",
            json={"question": "Which stack?", "options": ["React", "Vue", "Svelte"]},
            headers=h1,
        )
        assert created.status_code == status.HTTP_201_CREATED
        poll = created.json()
        assert poll["total_votes"] == 0
        assert poll["my_option_id"] is None

        react_id = [o for o in poll["options"] if o["text"] == "React"][0]["id"]
        vue_id = [o for o in poll["options"] if o["text"] == "Vue"][0]["id"]

        client.post(
            f"/api/v1/team-projects/{project_id}/polls/{poll['id']}/vote",
            json={"option_id": react_id},
            headers=h1,
        )
        client.post(
            f"/api/v1/team-projects/{project_id}/polls/{poll['id']}/vote",
            json={"option_id": vue_id},
            headers=h2,
        )
        # Bob changes his mind.
        client.post(
            f"/api/v1/team-projects/{project_id}/polls/{poll['id']}/vote",
            json={"option_id": react_id},
            headers=h2,
        )
        listed = client.get(
            f"/api/v1/team-projects/{project_id}/polls", headers=h1
        ).json()[0]
        counts = {o["text"]: o["votes"] for o in listed["options"]}
        assert counts == {"React": 2, "Vue": 0, "Svelte": 0}
        assert listed["total_votes"] == 2
        assert listed["my_option_id"] == react_id

        closed = client.post(
            f"/api/v1/team-projects/{project_id}/polls/{poll['id']}/close",
            headers=h1,
        )
        assert closed.json()["is_closed"] is True
        late = client.post(
            f"/api/v1/team-projects/{project_id}/polls/{poll['id']}/vote",
            json={"option_id": vue_id},
            headers=h2,
        )
        assert late.status_code == status.HTTP_409_CONFLICT

    def test_poll_validation(self, client):
        h1, _, project_id = self._two_member_team(client)
        too_few = client.post(
            f"/api/v1/team-projects/{project_id}/polls",
            json={"question": "Q?", "options": ["Only one"]},
            headers=h1,
        )
        assert too_few.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
