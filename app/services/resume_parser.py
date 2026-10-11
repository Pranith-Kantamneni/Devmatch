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
URL_RE = re.compile(
    r"https?://[^\s,)|>\]]+"
    r"|www\.[^\s,)|>\]]+"
    r"|[a-zA-Z0-9-]+\.[a-z]{2,}/[^\s,)|>\]]+"
)
BULLET_RE = re.compile(r"^\s*(?:[•·▪◦●○■□▸►→–—]|\-|\*|\+|\d+[.)])\s+")
TECH_LINE_RE = re.compile(
    r"^\s*(?:[•·▪◦●○■□▸►→\-*+]\s+)?"
    r"(?:tech(?:\s+stack|\s*nologies|\s*nical\s+stack)?|stack|built\s+with|tools?(?:\s+used)?)\s*[:|\-–—]",
    re.IGNORECASE,
)
TECH_LABEL_RE = re.compile(
    r"^(?:tech(?:\s+stack|\s*nologies)?|stack|built\s+with|tools?)\s*[:|\-–—]\s*",
    re.IGNORECASE,
)
PAREN_DATE_RE = re.compile(r"\((?:[^()]*\d{4}[^()]*)\)")
SHORT_SINGLE_LETTER_SKILLS = {"c", "r"}
# Ambiguous in free text ("go to", "C grades", ...): only trusted in skills sections.
SCAN_EXCLUDED_KEYWORDS = {"c", "r", "go", "cv"}
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
        return self._normalize_extracted_text("\n".join(parts))

    def _extract_docx(self, content: bytes) -> str:
        doc = Document(io.BytesIO(content))
        parts = [p.text for p in doc.paragraphs]
        # Skills/contact info often live in tables — don't ignore them.
        for table in doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))
        for section in doc.sections:
            for part in (section.header, section.footer):
                header_text = "\n".join(p.text for p in part.paragraphs).strip()
                if header_text:
                    parts.append(header_text)
        return self._normalize_extracted_text("\n".join(parts))

    @staticmethod
    def _normalize_extracted_text(text: str) -> str:
        # Join words hyphenated across PDF line breaks ("frame-\nwork" → "framework").
        text = re.sub(r"(\w)-\n(\w)", r"\1\2\n", text)
        # Normalize exotic bullets to "-".
        text = re.sub(r"^(\s*)[•·▪◦●○■□▸►→](\s+)", r"\1-\2", text, flags=re.MULTILINE)
        return text

    def _parse_text(self, text: str) -> ParsedResume:
        sections = self._split_sections(text)
        header = sections.get("header", "")

        full_name = self._extract_name(header, text)
        email = self._extract_email(text) or self._extract_email(header)
        phone = self._extract_phone(text)
        location = self._extract_location(text)
        summary = self._clean_block(sections.get("summary", "")) or None

        skills = self._parse_skills(sections.get("skills", ""))
        if len(skills) < 3:
            # Thin or missing skills section — recover known skills mentioned
            # in the summary/experience/projects text.
            scanned = self._scan_known_skills(
                "\n".join(
                    sections.get(name, "")
                    for name in ("summary", "experience", "projects")
                )
            )
            have = {s.name.lower() for s in skills}
            for name, category in scanned:
                if name.lower() not in have:
                    have.add(name.lower())
                    skills.append(
                        ParsedSkill(
                            name=name,
                            category=category,
                            proficiency=3,
                            years_experience=1.0,
                        )
                    )
                if len(skills) >= 40:
                    break
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
            if not name or len(name) > 40:
                continue
            if len(name) < 2 and name.lower() not in SHORT_SINGLE_LETTER_SKILLS:
                continue
            key = name.lower()
            if key in seen or key in NOISE_WORDS:
                continue
            if self._looks_like_number_or_year(name):
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

    @staticmethod
    def _looks_like_number_or_year(name: str) -> bool:
        cleaned = name.strip()
        # Pure numbers, years ("2021"), versions/quantities ("2+", "3.5", "5 years").
        if re.fullmatch(r"[\d\s.+,/x×-]+", cleaned):
            return True
        if re.fullmatch(r"(19|20)\d{2}", cleaned):
            return True
        if re.search(r"\b(years?|yrs?|months?|yoe)\b", cleaned, re.IGNORECASE):
            return True
        return False

    def _scan_known_skills(self, text: str) -> list[tuple[str, str]]:
        """Find catalogued skills mentioned in free text (preserving case)."""
        text = URL_RE.sub(" ", text)
        matches: list[tuple[int, int, str, str]] = []
        for category, keywords in SKILL_CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in SCAN_EXCLUDED_KEYWORDS:
                    continue
                for match in re.finditer(
                    r"\b" + re.escape(keyword) + r"\b", text, re.IGNORECASE
                ):
                    matches.append(
                        (match.start(), match.end(), match.group(0).strip(), category)
                    )
        # Longest match wins on overlap ("Node.js" beats "Node").
        matches.sort(key=lambda m: (m[0], -(m[1] - m[0])))
        kept: list[tuple[int, int, str, str]] = []
        for start, end, name, category in matches:
            if any(s <= start and end <= e for s, e, _, _ in kept):
                continue
            kept.append((start, end, name, category))
        found: list[tuple[str, str]] = []
        seen: set[str] = set()
        for _, _, name, category in kept:
            key = name.lower()
            if key not in seen:
                seen.add(key)
                found.append((name, category))
        return found

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

        for lines in self._split_entries(text, kind="experience"):
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
                    title = self._strip_bullet(line)
                elif not company and ("|" in line or " at " in line.lower()):
                    parts = re.split(r"\||\s+at\s+", line)
                    company = parts[0].strip() if len(parts) > 1 else None
                    if not company:
                        company = self._strip_bullet(line)
                else:
                    description_lines.append(self._strip_bullet(line))

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
        seen_titles: set[str] = set()

        for lines in self._split_entries(text, kind="project"):
            if not lines:
                continue
            title, tech, url = self._parse_project_header(lines[0])
            if not title:
                continue
            key = title.lower()
            if key in seen_titles:
                continue
            seen_titles.add(key)

            description_lines: list[str] = []
            for line in lines[1:]:
                tech_match = TECH_LINE_RE.match(line)
                if tech_match:
                    tech.extend(self._extract_tech_skills(line[tech_match.end():]))
                    continue
                for found_url in URL_RE.findall(line):
                    if url is None:
                        url = found_url if found_url.startswith("http") else f"https://{found_url}"
                cleaned = self._strip_bullet(line)
                # A bare tech list ("React, Node, MongoDB") is skills, not prose.
                if cleaned and self._looks_like_tech_list(cleaned):
                    tech.extend(self._extract_tech_skills(cleaned))
                    continue
                if cleaned:
                    description_lines.append(cleaned)

            # Recover tech mentioned anywhere in the entry.
            for name, _ in self._scan_known_skills("\n".join(lines)):
                tech.append(name)

            deduped_tech = list(dict.fromkeys(t for t in (s.strip() for s in tech) if t))
            entries.append(
                ParsedProject(
                    title=title,
                    description=self._clean_block("\n".join(description_lines)) or None,
                    skills=deduped_tech[:15],
                    url=url,
                )
            )

        return entries[:10]

    def _split_entries(self, text: str, kind: str) -> list[list[str]]:
        """Split a section into entries.

        Blank lines always split. Because PDF/DOCX extraction often drops
        blank lines, header-like lines also start a new entry: date-range
        lines, "Title | meta" / "Title – meta" lines, and (for projects)
        short title lines followed by a longer description line.
        """
        raw_lines = [line.rstrip() for line in text.split("\n")]
        # Drop empties but remember where blanks were.
        entries: list[list[str]] = []
        current: list[str] = []

        lines = [line.strip() for line in raw_lines]
        non_empty_idx = [i for i, line in enumerate(lines) if line]
        for pos, i in enumerate(non_empty_idx):
            line = lines[i]
            prev_blank = pos == 0 or non_empty_idx[pos - 1] != i - 1
            next_line = lines[non_empty_idx[pos + 1]] if pos + 1 < len(non_empty_idx) else None
            if current and (prev_blank or self._is_entry_header(line, next_line, kind)):
                entries.append(current)
                current = []
            current.append(line)
        if current:
            entries.append(current)
        return entries

    def _is_entry_header(self, line: str, next_line: str | None, kind: str) -> bool:
        stripped = self._strip_bullet(line)
        if not stripped or len(stripped) > 140:
            return False
        bulleted = bool(BULLET_RE.match(line))
        if "|" in stripped:
            left = stripped.split("|", 1)[0].strip()
            # A bare "a | b | c" skill list is not a header.
            if left and len(left) <= 80:
                return True
        if re.search(r"\s[–—]\s", stripped) and len(stripped) <= 120:
            return True
        if DATE_RE.search(stripped) or PAREN_DATE_RE.search(stripped):
            return True
        if bulleted:
            # Plain bullets are descriptions — never entry headers.
            return False
        if kind == "project" and next_line:
            nxt = self._strip_bullet(next_line)
            words = stripped.split()
            if (
                len(stripped) <= 70
                and len(words) <= 8
                and not stripped.endswith((".", ":", "?", "!"))
                and nxt
                and len(nxt) > len(stripped) + 15
            ):
                return True
        if kind == "experience" and re.search(r"\s+at\s+", stripped, re.IGNORECASE):
            return True
        return False

    @staticmethod
    def _strip_bullet(line: str) -> str:
        return BULLET_RE.sub("", line).strip()

    def _parse_project_header(self, line: str) -> tuple[str | None, list[str], str | None]:
        text = self._strip_bullet(line)
        url = None
        for found in URL_RE.findall(text):
            if url is None:
                url = found if found.startswith("http") else f"https://{found}"
        text = URL_RE.sub("", text)
        text = PAREN_DATE_RE.sub("", text)
        text = DATE_RE.sub("", text)
        tech: list[str] = []
        segments = [seg.strip(" |-–—") for seg in re.split(r"\s*\|\s*", text)]
        title = segments[0].strip() if segments else ""
        title = re.sub(r"\s+", " ", title).strip(" -–—:,")
        for segment in segments[1:]:
            if segment:
                tech.extend(self._extract_tech_skills(segment))
        if not title:
            return None, [], url
        return title, tech, url

    def _extract_tech_skills(self, text: str) -> list[str]:
        parts = re.split(r"[,;•·|/]+", text)
        skills = []
        for part in parts:
            name = self._clean_skill(TECH_LABEL_RE.sub("", part))
            if not name or len(name) > 40:
                continue
            if len(name) < 2 and name.lower() not in SHORT_SINGLE_LETTER_SKILLS:
                continue
            if self._looks_like_number_or_year(name) or name.lower() in NOISE_WORDS:
                continue
            skills.append(name)
        return skills

    def _looks_like_tech_list(self, line: str) -> bool:
        if "|" in line or len(line) > 120:
            return False
        parts = [p.strip() for p in re.split(r"[,;•·/]+", line) if p.strip()]
        if len(parts) < 2:
            return False
        if any(len(p) > 30 or len(p.split()) > 4 for p in parts):
            return False
        # At least one recognizable skill — avoids eating real sentences.
        return any(self._infer_category(p) != "other" for p in parts)

    def _clean_block(self, text: str) -> str:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        return "\n".join(lines).strip()
