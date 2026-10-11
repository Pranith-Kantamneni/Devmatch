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


class TestMultiProjectParsing:
    """Regression tests: resumes without blank lines must still split entries."""

    NO_BLANK_LINES = b"""John Doe
john@example.com
PROJECTS
E-Commerce Platform | React, Node.js, MongoDB | github.com/john/shop
- Built cart and payments with Stripe
- Deployed with Docker on AWS
Chat Application | Socket.io, Express, Redis
- Real-time messaging for 10k users
- Tech: Socket.io, Express, Redis
Portfolio Website
Personal site with blog. Built with Next.js and Tailwind.
"""

    def test_all_projects_parsed_without_blank_lines(self):
        svc = ResumeParserService()
        result = svc.parse(self.NO_BLANK_LINES, "resume.txt")
        titles = [p.title for p in result.projects]
        assert titles == [
            "E-Commerce Platform",
            "Chat Application",
            "Portfolio Website",
        ]

    def test_project_tech_and_url_extracted(self):
        svc = ResumeParserService()
        result = svc.parse(self.NO_BLANK_LINES, "resume.txt")
        shop = result.projects[0]
        assert "React" in shop.skills
        assert "MongoDB" in shop.skills
        assert shop.url and "github.com/john/shop" in shop.url
        chat = result.projects[1]
        assert "Socket.io" in chat.skills or "Redis" in chat.skills
        site = result.projects[2]
        assert "Next.js" in site.skills or "Tailwind" in site.skills

    def test_experience_splits_without_blank_lines(self):
        svc = ResumeParserService()
        result = svc.parse(
            b"EXPERIENCE\nBackend Engineer at Acme, Jan 2021 - Present\n- Built APIs\n"
            b"Frontend Engineer at Beta, Jun 2019 - Dec 2020\n- Built dashboards\n",
            "resume.txt",
        )
        assert [(e.title, e.company) for e in result.experience] == [
            ("Backend Engineer", "Acme"),
            ("Frontend Engineer", "Beta"),
        ]

    def test_digit_skills_kept(self):
        svc = ResumeParserService()
        result = svc.parse(b"SKILLS\nPython, HTML5, React, OAuth2, C", "resume.txt")
        names = {s.name for s in result.skills}
        assert {"Python", "HTML5", "React", "OAuth2", "C"} <= names

    def test_years_not_parsed_as_skills(self):
        svc = ResumeParserService()
        result = svc.parse(b"SKILLS\nPython, 2021, 3+ years, React", "resume.txt")
        names = {s.name for s in result.skills}
        assert "Python" in names and "React" in names
        assert "2021" not in names
        assert not any("years" in n for n in names)

    def test_known_skills_recovered_without_skills_section(self):
        svc = ResumeParserService()
        result = svc.parse(
            b"SUMMARY\nBackend engineer.\nEXPERIENCE\nBuilt services with Python and Docker.\n",
            "resume.txt",
        )
        names = {s.name for s in result.skills}
        assert "Python" in names and "Docker" in names
