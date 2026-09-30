import io
import re

from docx import Document
from pypdf import PdfReader

from app.schemas.resume import (
    ParsedEducation,
    ParsedExperience,
    ParsedProject,
    ParsedResume,
    ParsedSkill,
)

SECTION_HEADERS = {
    "summary": [
        "summary", "objective", "objectives", "about", "about me", "profile",
        "professional summary", "career objective", "personal statement",
    ],
    "experience": [
        "experience", "work experience", "employment", "employment history",
        "work history", "professional experience", "relevant experience",
        "career history", "professional background",
    ],
    "education": [
        "education", "academic", "academic background", "academic history",
        "qualifications", "educational background", "education and training",
    ],
    "skills": [
        "skills", "technical skills", "technical skill", "technologies",
        "tech stack", "technology stack", "technical expertise", "core competencies",
        "competencies", "technical proficiencies", "key skills", "skill set",
        "languages and tools", "tools and technologies", "programming languages",
    ],
    "projects": [
        "projects", "personal projects", "side projects", "selected projects",
        "academic projects", "key projects", "notable projects", "project experience",
    ],
    "certifications": [
        "certifications", "certificates", "licenses", "credentials",
    ],
    "awards": [
        "awards", "honors", "honours", "achievements", "accomplishments",
    ],
    "languages": ["languages", "language skills"],
    "interests": ["interests", "hobbies", "activities", "extra curricular"],
}

HEADER_ALIASES = {}
for section, headers in SECTION_HEADERS.items():
    for header in headers:
        HEADER_ALIASES[header] = section

SKILL_CATEGORY_KEYWORDS = {
    "language": [
        "python", "java", "javascript", "typescript", "c++", "c#", "c", "go", "golang",
        "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl",
        "haskell", "elixir", "erlang", "dart", "lua", "shell", "bash", "sql",
        "html", "css", "sass", "less", "graphql", "r", "julia", "groovy",
    ],
        "framework": [
        "react", "angular", "vue", "svelte", "next.js", "nextjs", "nuxt", "django",
        "flask", "fastapi", "spring", "spring boot", "express", "express.js", "rails",
        "laravel", "symfony", "asp.net", "dotnet", ".net", "flutter", "react native",
        "electron", "tauri", "jquery", "bootstrap", "tailwind", "django",
        "node.js", "node", "nestjs", "nest.js", "fastify", "hapi", "koa",
        "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn", "pandas",
        "numpy", "scipy", "matplotlib", "seaborn", "xgboost", "lightgbm", "hugging face",
    ],
    "tool": [
        "git", "github", "gitlab", "docker", "kubernetes", "k8s", "aws", "azure",
        "gcp", "google cloud", "jenkins", "terraform", "ansible", "linux", "unix",
        "mongodb", "postgresql", "mysql", "sqlite", "redis", "elasticsearch",
        "kafka", "rabbitmq", "nginx", "apache", "firebase", "supabase", "heroku",
        "vercel", "netlify", "jira", "confluence", "figma", "postman", "vscode",
        "intellij", "pycharm", "tableau", "power bi", "excel", "hadoop", "spark",
        "airflow", "dbt", "snowflake", "databricks", "selenium", "cypress",
        "jest", "pytest", "junit", "maven", "gradle", "npm", "yarn", "webpack",
        "vite", "babel", "eslint", "prettier", "ci/cd", "github actions",
    ],
    "domain": [
        "machine learning", "deep learning", "artificial intelligence", "ai",
        "data science", "data analysis", "data engineering", "web development",
        "web dev", "frontend", "front-end", "backend", "back-end", "full stack",
        "fullstack", "mobile", "android", "ios", "devops", "cloud", "security",
        "cybersecurity", "blockchain", "web3", "nlp", "computer vision", "cv",
        "robotics", "iot", "embedded", "game development", "ui/ux", "ui", "ux",
        "product management", "agile", "scrum", "testing", "qa", "automation",
    ],
}

NOISE_WORDS = {
    "and", "or", "the", "a", "an", "of", "in", "on", "at", "to", "for", "with",
    "by", "from", "as", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "this", "that", "these", "those",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it", "they",
    "work", "working", "worked", "team", "teams", "role", "responsibilities",
    "responsible", "ability", "strong", "good", "experience", "years", "year",
    "using", "used", "use", "including", "include", "includes", "various",
    "related", "etc", "skills", "skill", "tools", "technologies", "technology",
}

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(\(?\+?\d[\d\s().-]{7,}\d\)?)")
DATE_RE = re.compile(
    r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,]*\d{4}"
    r"|\d{4}|present|current|now)"
    r"\s*(?:-|–|to|until)\s*"
    r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,]*\d{4}"
    r"|\d{4}|present|current|now)",
    re.IGNORECASE,
)


class ResumeParserService:
    def parse(self, content: bytes, filename: str) -> ParsedResume:
        text = self._extract_text(content, filename)
        if not text or not text.strip():
            return ParsedResume(
                note="Could not extract text from this file. Try a PDF, DOCX, or TXT resume."
            )
        return self._parse_text(text)

    def _extract_text(self, content: bytes, filename: str) -> str:
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        if ext == "pdf":
            return self._extract_pdf(content)
        if ext in ("docx", "doc"):
            return self._extract_docx(content)
        if ext in ("txt", "md", "text", "rtf"):
            return content.decode("utf-8", errors="ignore")
        return content.decode("utf-8", errors="ignore")

    def _extract_pdf(self, content: bytes) -> str:
        reader = PdfReader(io.BytesIO(content))
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts)

    def _extract_docx(self, content: bytes) -> str:
        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)

    def _parse_text(self, text: str) -> ParsedResume:
        sections = self._split_sections(text)
        header = sections.get("header", "")

        full_name = self._extract_name(header, text)
        email = self._extract_email(text) or self._extract_email(header)
        phone = self._extract_phone(text)
        location = self._extract_location(text)
        summary = self._clean_block(sections.get("summary", "")) or None

        skills = self._parse_skills(sections.get("skills", ""))
        experience = self._parse_experience(sections.get("experience", ""))
        education = self._parse_education(sections.get("education", ""))
        projects = self._parse_projects(sections.get("projects", ""))

        return ParsedResume(
            full_name=full_name,
            email=email,
            phone=phone,
            location=location,
            summary=summary,
            skills=skills,
            experience=experience,
            education=education,
            projects=projects,
        )

    def _split_sections(self, text: str) -> dict[str, str]:
        lines = text.split("\n")
        sections: dict[str, list[str]] = {"header": []}
        current = "header"

        for line in lines:
            header, remainder = self._match_header(line)
            if header:
                current = header
                sections.setdefault(current, [])
                if remainder:
                    sections[current].append(remainder)
            else:
                sections.setdefault(current, []).append(line)

        return {key: "\n".join(value) for key, value in sections.items()}

    def _match_header(self, line: str) -> tuple[str | None, str | None]:
        stripped = line.strip()
        if ":" in stripped:
            head, _, rest = stripped.partition(":")
            section = self._lookup_header(head)
            if section:
                return section, rest.strip() or None
        section = self._lookup_header(stripped)
        if section:
            return section, None
        return None, None

    def _lookup_header(self, text: str) -> str | None:
        cleaned = text.strip().lower()
        cleaned = cleaned.replace(":", "").replace(".", "")
        cleaned = re.sub(r"^[\s\-–—*#=]+", "", cleaned)
        cleaned = re.sub(r"[\s\-–—*#=]+$", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned or len(cleaned) > 40:
            return None
        return HEADER_ALIASES.get(cleaned)

    def _extract_name(self, header: str, text: str) -> str | None:
        for line in header.split("\n"):
            candidate = line.strip()
            candidate = re.sub(r"^[\s\-–—*#]+", "", candidate)
            candidate = re.sub(r"[\s\-–—*#]+$", "", candidate)
            if not candidate:
                continue
            if EMAIL_RE.search(candidate) or PHONE_RE.search(candidate):
                continue
            words = candidate.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
                if not any(c.isdigit() for c in candidate):
                    return candidate
        first_line = text.strip().split("\n")[0].strip()
        if first_line and not EMAIL_RE.search(first_line) and len(first_line) < 50:
            return first_line
        return None

    def _extract_email(self, text: str) -> str | None:
        match = EMAIL_RE.search(text)
        return match.group(0) if match else None

    def _extract_phone(self, text: str) -> str | None:
        match = PHONE_RE.search(text)
        return match.group(0).strip() if match else None

    def _extract_location(self, text: str) -> str | None:
        location_re = re.compile(
            r"\b([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*,\s*[A-Z]{2}(?:\s\d{5})?)\b"
        )
        for line in text.split("\n"):
            match = location_re.search(line)
            if match:
                return match.group(1)
        for line in text.split("\n"):
            if re.search(r"\b(location|address|city|based in)\b", line, re.IGNORECASE):
                cleaned = re.sub(
                    r".*?(location|address|city|based in)\s*:\s*", "", line, flags=re.IGNORECASE
                ).strip()
                if cleaned and len(cleaned) < 60:
                    return cleaned
        return None

    def _parse_skills(self, text: str) -> list[ParsedSkill]:
        if not text.strip():
            return []
        parts = re.split(r"[,;•·|\n]+", text)
        skills: list[ParsedSkill] = []
        seen: set[str] = set()

        for part in parts:
            name = self._clean_skill(part)
            if not name or len(name) < 2 or len(name) > 40:
                continue
            key = name.lower()
            if key in seen or key in NOISE_WORDS:
                continue
            if any(char.isdigit() for char in name):
                continue
            seen.add(key)
            skills.append(
                ParsedSkill(
                    name=name,
                    category=self._infer_category(name),
                    proficiency=3,
                    years_experience=1.0,
                )
            )

        return skills[:40]

    def _clean_skill(self, text: str) -> str:
        cleaned = text.strip()
        cleaned = re.sub(r"^[\s\-–—*#●▪◦·•]+", "", cleaned)
        cleaned = re.sub(r"[\s\-–—*#●▪◦·•]+$", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    def _infer_category(self, skill: str) -> str:
        lowered = skill.lower()
        for category, keywords in SKILL_CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if re.search(r"\b" + re.escape(keyword) + r"\b", lowered):
                    return category
        return "other"

    def _parse_experience(self, text: str) -> list[ParsedExperience]:
        if not text.strip():
            return []
        entries: list[ParsedExperience] = []
        blocks = re.split(r"\n\s*\n", text)

        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines:
                continue
            duration = None
            title = None
            company = None
            description_lines = []

            for line in lines:
                date_match = DATE_RE.search(line)
                if date_match and not duration:
                    duration = re.sub(r"\s+", " ", date_match.group(0)).strip()
                    remainder = DATE_RE.sub("", line).strip(" |,-–—")
                    if remainder:
                        at_parts = re.split(r"\s+at\s+", remainder, maxsplit=1)
                        if len(at_parts) == 2 and not title and not company:
                            title, company = at_parts[0].strip(), at_parts[1].strip()
                        elif not title:
                            title = remainder
                        elif not company:
                            company = remainder
                    continue
                if not title:
                    title = line
                elif not company and ("|" in line or " at " in line.lower()):
                    parts = re.split(r"\||\s+at\s+", line)
                    company = parts[0].strip() if len(parts) > 1 else None
                    if not company:
                        company = line
                else:
                    description_lines.append(line)

            if title:
                entries.append(
                    ParsedExperience(
                        title=title,
                        company=company,
                        duration=duration,
                        description=self._clean_block("\n".join(description_lines)) or None,
                    )
                )

        return entries[:10]

    def _parse_education(self, text: str) -> list[ParsedEducation]:
        if not text.strip():
            return []
        entries: list[ParsedEducation] = []
        blocks = re.split(r"\n\s*\n", text)

        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines:
                continue
            degree = lines[0] if lines else None
            institution = None
            year = None

            for line in lines[1:]:
                year_match = re.search(r"\b(19|20)\d{2}\b", line)
                if year_match and not year:
                    year = year_match.group(0)
                elif not institution:
                    institution = line

            if degree:
                entries.append(
                    ParsedEducation(degree=degree, institution=institution, year=year)
                )

        return entries[:5]

    def _parse_projects(self, text: str) -> list[ParsedProject]:
        if not text.strip():
            return []
        entries: list[ParsedProject] = []
        blocks = re.split(r"\n\s*\n", text)

        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines:
                continue
            title = lines[0]
            description = self._clean_block("\n".join(lines[1:])) or None
            entries.append(ParsedProject(title=title, description=description))

        return entries[:10]

    def _clean_block(self, text: str) -> str:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        return "\n".join(lines).strip()
