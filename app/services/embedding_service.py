import hashlib
import re

import numpy as np

from app.core.config import Settings
from app.db.models.skill import SkillCategory

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class EmbeddingService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.dimension = settings.EMBEDDING_DIMENSION

    def build_tokens(self, profile, user_skills, projects) -> list[str]:
        tokens: list[str] = []

        for user_skill in user_skills:
            weight = self._category_weight(user_skill.skill.category)
            tokens.extend(
                [user_skill.skill.name.lower()] * max(1, int(round(weight)))
            )

        for project in projects:
            weight = max(1, int(round(self.settings.EMBEDDING_PROJECT_WEIGHT)))
            tokens.extend([project.title.lower()] * weight)
            if project.description:
                tokens.append(project.description.lower())

        if profile is not None and profile.bio:
            tokens.append(profile.bio.lower())

        return tokens

    def _category_weight(self, category: SkillCategory) -> float:
        if category in (SkillCategory.LANGUAGE, SkillCategory.FRAMEWORK):
            return self.settings.EMBEDDING_SKILL_WEIGHT
        if category == SkillCategory.TOOL:
            return self.settings.EMBEDDING_TECHNOLOGY_WEIGHT
        if category == SkillCategory.DOMAIN:
            return self.settings.EMBEDDING_DOMAIN_WEIGHT
        return self.settings.EMBEDDING_SKILL_WEIGHT

    def embed_tokens(self, tokens: list[str]) -> list[float]:
        vector = np.zeros(self.dimension, dtype=np.float64)

        for token in tokens:
            for word in _TOKEN_RE.findall(token):
                vector[self._hash_index(word)] += 1.0

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector /= norm

        return vector.tolist()

    def embed_text(self, text: str) -> list[float]:
        return self.embed_tokens([text])

    def embed_profile(self, profile, user_skills, projects) -> list[float]:
        return self.embed_tokens(self.build_tokens(profile, user_skills, projects))

    def build_team_project_tokens(self, team_project, required_skills) -> list[str]:
        tokens: list[str] = []

        for link in required_skills:
            weight = self._category_weight(link.skill.category)
            tokens.extend(
                [link.skill.name.lower()] * max(1, int(round(weight)))
            )

        for tech in team_project.tech_stack or []:
            weight = max(1, int(round(self.settings.EMBEDDING_TECHNOLOGY_WEIGHT)))
            tokens.extend([tech.lower()] * weight)

        if team_project.description:
            tokens.extend(
                [team_project.description.lower()]
                * max(1, int(round(self.settings.EMBEDDING_PROJECT_WEIGHT)))
            )

        return tokens

    def embed_team_project(self, team_project, required_skills) -> list[float]:
        return self.embed_tokens(
            self.build_team_project_tokens(team_project, required_skills)
        )

    def _hash_index(self, token: str) -> int:
        digest = hashlib.md5(token.encode("utf-8")).hexdigest()
        return int(digest, 16) % self.dimension

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        vec_a = np.asarray(a, dtype=np.float64)
        vec_b = np.asarray(b, dtype=np.float64)

        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))
