from fastapi import status

from app.core.config import get_settings
from app.services.embedding_service import EmbeddingService
from conftest import create_user_with_token


def make_user(client, username, email, skills, level="senior", bio="developer"):
    headers = create_user_with_token(client, username, email)
    client.put(
        "/api/v1/profiles/me",
        json={"full_name": username, "bio": bio, "experience_level": level},
        headers=headers,
    )
    for skill in skills:
        client.post(
            "/api/v1/profiles/me/skills",
            json={"name": skill, "category": "language", "proficiency": 4},
            headers=headers,
        )
    return headers


class TestEmbeddingGeneration:
    def test_embedding_is_deterministic(self):
        settings = get_settings()
        service = EmbeddingService(settings)
        text = "python fastapi postgresql machine learning"
        assert service.embed_text(text) == service.embed_text(text)

    def test_embedding_dimension(self):
        settings = get_settings()
        service = EmbeddingService(settings)
        vector = service.embed_text("python fastapi")
        assert len(vector) == settings.EMBEDDING_DIMENSION

    def test_embedding_is_normalized(self):
        settings = get_settings()
        service = EmbeddingService(settings)
        vector = service.embed_text("python fastapi postgresql")
        magnitude = sum(x * x for x in vector) ** 0.5
        assert abs(magnitude - 1.0) < 1e-9

    def test_embedding_empty_text(self):
        settings = get_settings()
        service = EmbeddingService(settings)
        vector = service.embed_text("")
        assert all(x == 0.0 for x in vector)

    def test_embedding_different_text_different_vector(self):
        settings = get_settings()
        service = EmbeddingService(settings)
        v1 = service.embed_text("python fastapi")
        v2 = service.embed_text("java spring")
        assert v1 != v2


class TestCosineSimilarity:
    def test_identical_vectors(self):
        settings = get_settings()
        service = EmbeddingService(settings)
        vector = service.embed_text("python fastapi")
        assert abs(service.cosine_similarity(vector, vector) - 1.0) < 1e-9

    def test_orthogonal_vectors(self):
        service = EmbeddingService(get_settings())
        assert service.cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0

    def test_partial_similarity(self):
        service = EmbeddingService(get_settings())
        score = service.cosine_similarity([1.0, 1.0], [1.0, 0.0])
        assert 0.0 < score < 1.0

    def test_zero_vector(self):
        service = EmbeddingService(get_settings())
        assert service.cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


class TestRecommendations:
    def test_recommendations_require_auth(self, client):
        response = client.get("/api/v1/recommendations")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_recommendations_empty_when_no_other_profiles(self, client):
        headers = make_user(client, "alice", "alice@example.com", ["Python"])
        response = client.get("/api/v1/recommendations", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["recommendations"] == []
        assert data["total_candidates"] == 0

    def test_recommendations_exclude_self(self, client):
        headers = make_user(client, "alice", "alice@example.com", ["Python"])
        make_user(client, "bob", "bob@example.com", ["Python"])
        response = client.get("/api/v1/recommendations", headers=headers)
        data = response.json()
        usernames = [r["user"]["username"] for r in data["recommendations"]]
        assert "alice" not in usernames
        assert "bob" in usernames

    def test_recommendations_ranking(self, client):
        headers = make_user(
            client, "alice", "alice@example.com", ["Python", "FastAPI", "PostgreSQL"]
        )
        make_user(
            client, "bob", "bob@example.com", ["Python", "FastAPI", "PostgreSQL"]
        )
        make_user(client, "carol", "carol@example.com", ["Java", "Spring", "Kafka"])
        response = client.get("/api/v1/recommendations", headers=headers)
        data = response.json()
        assert len(data["recommendations"]) == 2
        assert data["recommendations"][0]["user"]["username"] == "bob"
        assert data["recommendations"][1]["user"]["username"] == "carol"
        assert (
            data["recommendations"][0]["similarity_score"]
            > data["recommendations"][1]["similarity_score"]
        )

    def test_recommendations_top_k(self, client):
        headers = make_user(client, "alice", "alice@example.com", ["Python"])
        for i in range(5):
            make_user(client, f"user{i}", f"user{i}@example.com", ["Python"])
        response = client.get("/api/v1/recommendations?limit=3", headers=headers)
        data = response.json()
        assert len(data["recommendations"]) == 3
        assert data["total_candidates"] == 5

    def test_recommendations_default_limit(self, client):
        headers = make_user(client, "alice", "alice@example.com", ["Python"])
        for i in range(15):
            make_user(client, f"user{i}", f"user{i}@example.com", ["Python"])
        response = client.get("/api/v1/recommendations", headers=headers)
        data = response.json()
        assert len(data["recommendations"]) == get_settings().MATCHING_DEFAULT_LIMIT

    def test_recommendations_limit_validation(self, client):
        headers = make_user(client, "alice", "alice@example.com", ["Python"])
        response = client.get("/api/v1/recommendations?limit=0", headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_recommendations_returns_skill_overlap(self, client):
        headers = make_user(
            client, "alice", "alice@example.com", ["Python", "FastAPI", "PostgreSQL"]
        )
        make_user(client, "bob", "bob@example.com", ["Python", "Django"])
        response = client.get("/api/v1/recommendations", headers=headers)
        data = response.json()
        overlap = data["recommendations"][0]["skill_overlap"]
        assert "python" in overlap

    def test_recommendations_no_profile(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        make_user(client, "bob", "bob@example.com", ["Python"])
        response = client.get("/api/v1/recommendations", headers=headers)
        data = response.json()
        assert data["recommendations"] == []
        assert data["total_candidates"] == 0

    def test_recommendations_multiple_candidates(self, client):
        headers = make_user(client, "alice", "alice@example.com", ["Python"])
        make_user(client, "bob", "bob@example.com", ["Python", "Django"])
        make_user(client, "carol", "carol@example.com", ["JavaScript", "React"])
        make_user(client, "dave", "dave@example.com", ["Python", "FastAPI"])
        response = client.get(
            "/api/v1/recommendations?limit=10", headers=headers
        )
        data = response.json()
        assert data["total_candidates"] == 3
        assert len(data["recommendations"]) == 3
        scores = [r["similarity_score"] for r in data["recommendations"]]
        assert scores == sorted(scores, reverse=True)
