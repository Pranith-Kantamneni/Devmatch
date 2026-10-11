from fastapi import status

from app.data.colleges import (
    canonical_college_id,
    resolve_college,
    resolve_input,
    same_college,
    search_colleges,
)
from conftest import create_user_with_token


class TestDirectory:
    def test_abbreviation_resolves(self):
        assert resolve_college("VIT")["id"] == "vit-vellore"
        assert resolve_college("Vellore Institute of Technology")["id"] == "vit-vellore"
        assert resolve_college("IITB")["id"] == "iit-bombay"
        assert resolve_college("NIT Trichy")["id"] == "nit-trichy"

    def test_campuses_are_distinct(self):
        assert resolve_college("VIT Vellore")["id"] == "vit-vellore"
        assert resolve_college("VIT Chennai")["id"] == "vit-chennai"
        assert not same_college("VIT Vellore", None, "VIT Chennai", None)

    def test_unknown_returns_none(self):
        assert resolve_college("Hogwarts School") is None
        assert resolve_college("") is None
        assert resolve_college(None) is None

    def test_same_college_variants(self):
        assert same_college("VIT", None, "Vellore Institute of Technology", None)
        assert same_college("iit bombay", None, "Indian Institute of Technology Bombay", None)
        assert same_college(None, "vit-vellore", "VIT", None)
        assert not same_college("VIT", None, "SRM", None)
        assert not same_college(None, None, None, None)
        # Identical custom text still matches.
        assert same_college("Hogwarts", None, "hogwarts ", None)

    def test_custom_namespace(self):
        assert canonical_college_id("Hogwarts") == "custom:hogwarts"
        assert canonical_college_id(None) is None

    def test_resolve_input(self):
        cid, name = resolve_input("vit-vellore", "whatever")
        assert (cid, name) == ("vit-vellore", "Vellore Institute of Technology, Vellore")
        cid, name = resolve_input(None, "IITB")
        assert cid == "iit-bombay"
        cid, name = resolve_input(None, "Hogwarts")
        assert (cid, name) == (None, "Hogwarts")
        assert resolve_input(None, None) == (None, None)
        try:
            resolve_input("nope-not-real", None)
            raise AssertionError("should have raised")
        except ValueError:
            pass

    def test_search_ranking(self):
        assert search_colleges("vit")[0]["id"] == "vit-vellore"
        assert search_colleges("manipal")[0]["id"] == "mit-manipal"
        assert any(e["id"] == "iit-bombay" for e in search_colleges("bombay"))
        assert search_colleges("x") == []
        assert len(search_colleges("college", limit=3)) <= 3


class TestMetaEndpoints:
    def test_colleges_search(self, client):
        response = client.get("/api/v1/meta/colleges", params={"q": "vit"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 300
        assert data["colleges"][0]["id"] == "vit-vellore"

    def test_colleges_featured_without_query(self, client):
        response = client.get("/api/v1/meta/colleges")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["colleges"]) > 0

    def test_branches(self, client):
        response = client.get("/api/v1/meta/branches")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Computer Science and Engineering" in data["branches"]
        assert data["total"] == len(data["branches"])


class TestProfileCollege:
    def test_college_id_roundtrip(self, client):
        headers = create_user_with_token(client, "col_alice", "col_alice@example.com")
        response = client.put(
            "/api/v1/profiles/me",
            json={"college_id": "vit-vellore", "branch": "Computer Science and Engineering"},
            headers=headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["college_id"] == "vit-vellore"
        assert data["college"] == "Vellore Institute of Technology, Vellore"
        assert data["branch"] == "Computer Science and Engineering"

    def test_college_text_auto_resolves(self, client):
        headers = create_user_with_token(client, "col_bob", "col_bob@example.com")
        response = client.put(
            "/api/v1/profiles/me", json={"college": "VIT"}, headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["college_id"] == "vit-vellore"
        assert data["college"] == "Vellore Institute of Technology, Vellore"

    def test_custom_college_kept(self, client):
        headers = create_user_with_token(client, "col_cid", "col_cid@example.com")
        response = client.put(
            "/api/v1/profiles/me", json={"college": "Hogwarts"}, headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["college_id"] is None
        assert data["college"] == "Hogwarts"

    def test_unknown_college_id_rejected(self, client):
        headers = create_user_with_token(client, "col_dan", "col_dan@example.com")
        response = client.put(
            "/api/v1/profiles/me", json={"college_id": "nope"}, headers=headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestSameCollegeVariants:
    def _team(self, client, headers, **kwargs):
        payload = {
            "title": "Same College Hack",
            "max_members": 4,
            "require_same_college": True,
            **kwargs,
        }
        return client.post("/api/v1/team-projects", json=payload, headers=headers)

    def test_variant_spellings_match(self, client):
        from test_team_projects import make_user

        h1 = make_user(client, "scc_alice", "scc_alice@example.com")
        h2 = make_user(client, "scc_bob", "scc_bob@example.com")
        # Alice picks from the directory, Bob types the abbreviation.
        client.put(
            "/api/v1/profiles/me", json={"college_id": "vit-vellore"}, headers=h1
        )
        client.put("/api/v1/profiles/me", json={"college": "VIT"}, headers=h2)
        project_id = self._team(
            client, h1, college_id="vit-vellore"
        ).json()["id"]
        # Bob's variant spelling is accepted.
        response = client.post(
            f"/api/v1/team-projects/{project_id}/apply", json={}, headers=h2
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_different_campus_rejected(self, client):
        from test_team_projects import make_user

        h1 = make_user(client, "scc2_alice", "scc2_alice@example.com")
        h2 = make_user(client, "scc2_bob", "scc2_bob@example.com")
        client.put(
            "/api/v1/profiles/me", json={"college_id": "vit-vellore"}, headers=h1
        )
        client.put(
            "/api/v1/profiles/me", json={"college_id": "vit-chennai"}, headers=h2
        )
        project_id = self._team(
            client, h1, college_id="vit-vellore"
        ).json()["id"]
        response = client.post(
            f"/api/v1/team-projects/{project_id}/apply", json={}, headers=h2
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_team_text_auto_resolves(self, client):
        from test_team_projects import make_user

        h1 = make_user(client, "scc3_alice", "scc3_alice@example.com")
        project = self._team(client, h1, college="IITB").json()
        assert project["college_id"] == "iit-bombay"
        assert project["college"] == "Indian Institute of Technology Bombay"
