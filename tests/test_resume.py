from fastapi import status

from app.services.resume_parser import ResumeParserService
from conftest import create_user_with_token

SAMPLE_RESUME = b"""Jane Smith
Full-stack Developer
New York, NY
jane@email.com | (555) 987-6543

SUMMARY
Passionate developer who loves hackathons.

SKILLS
Python, React, TypeScript, PostgreSQL, Docker

EXPERIENCE
Software Engineer
Acme Corp | Jan 2022 - Present
- Built scalable web apps

EDUCATION
B.S. Computer Science
MIT 2018 - 2022

PROJECTS
Hackathon Winner 2023
- Built an AI-powered app
"""


class TestParseResumeEndpoint:
    def test_parse_txt_resume(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        response = client.post(
            "/api/v1/profiles/me/parse-resume",
            files={"file": ("resume.txt", SAMPLE_RESUME, "text/plain")},
            headers=headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "Jane Smith"
        assert data["email"] == "jane@email.com"
        assert data["location"] == "New York, NY"
        assert len(data["skills"]) == 5
        assert {s["name"] for s in data["skills"]} == {
            "Python", "React", "TypeScript", "PostgreSQL", "Docker"
        }

    def test_defaults_note_and_values(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        response = client.post(
            "/api/v1/profiles/me/parse-resume",
            files={"file": ("resume.txt", SAMPLE_RESUME, "text/plain")},
            headers=headers,
        )
        data = response.json()
        assert "3" in data["note"] and "1" in data["note"]
        for skill in data["skills"]:
            assert skill["proficiency"] == 3
            assert skill["years_experience"] == 1.0

    def test_unsupported_file_type(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        response = client.post(
            "/api/v1/profiles/me/parse-resume",
            files={"file": ("resume.exe", b"data", "application/octet-stream")},
            headers=headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_parse_requires_auth(self, client):
        response = client.post(
            "/api/v1/profiles/me/parse-resume",
            files={"file": ("resume.txt", SAMPLE_RESUME, "text/plain")},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestResumeParserService:
    def test_inline_section_headers(self):
        svc = ResumeParserService()
        result = svc.parse(
            b"SKILLS: Python, TensorFlow, SQL\nEXPERIENCE: ML Engineer at OpenAI, 2021 - Present",
            "resume.txt",
        )
        assert {s.name for s in result.skills} == {"Python", "TensorFlow", "SQL"}
        assert result.experience[0].title == "ML Engineer"
        assert result.experience[0].company == "OpenAI"

    def test_skill_categories(self):
        svc = ResumeParserService()
        result = svc.parse(b"SKILLS\nPython, React, Docker, Machine Learning", "resume.txt")
        by_name = {s.name: s.category for s in result.skills}
        assert by_name["Python"] == "language"
        assert by_name["React"] == "framework"
        assert by_name["Docker"] == "tool"
        assert by_name["Machine Learning"] == "domain"

    def test_empty_file_returns_note(self):
        svc = ResumeParserService()
        result = svc.parse(b"   \n  ", "resume.txt")
        assert result.skills == []
        assert result.note

    def test_save_parsed_skills_to_profile(self, client):
        headers = create_user_with_token(client, "alice", "alice@example.com")
        parsed = client.post(
            "/api/v1/profiles/me/parse-resume",
            files={"file": ("resume.txt", SAMPLE_RESUME, "text/plain")},
            headers=headers,
        ).json()
        for skill in parsed["skills"][:2]:
            resp = client.post("/api/v1/profiles/me/skills", json=skill, headers=headers)
            assert resp.status_code == status.HTTP_201_CREATED
        profile = client.get("/api/v1/profiles/me", headers=headers).json()
        assert len(profile["skills"]) == 2
