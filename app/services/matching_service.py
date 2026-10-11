from datetime import datetime, timezone
import re

from sqlalchemy.orm import Session

from app.core import cache as result_cache
from app.core.config import Settings
from app.core.exceptions import ForbiddenException, NotFoundException
from app.db.models.profile import DeveloperProfile, ExperienceLevel
from app.repositories.profile_repository import ProfileRepository
from app.repositories.team_project_repository import TeamProjectRepository
from app.schemas.recommendation import (
    Recommendation,
    RecommendationListResponse,
)
from app.schemas.team_project import (
    ProjectRecommendation,
    ProjectRecommendationListResponse,
    SkillEvidence,
)
from app.schemas.user import PublicUserResponse
from app.services.embedding_service import EmbeddingService
from app.utils.mappers import to_public_profile_response

_EXPERIENCE_ORDER = [
    ExperienceLevel.STUDENT,
    ExperienceLevel.JUNIOR,
    ExperienceLevel.MID,
    ExperienceLevel.SENIOR,
    ExperienceLevel.LEAD,
]

SKILL_ALIASES = {
    "js": "javascript",
    "ts": "typescript",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "node": "node.js",
    "nextjs": "next.js",
    "vuejs": "vue",
    "vue.js": "vue",
    "postgres": "postgresql",
    "psql": "postgresql",
    "mongo": "mongodb",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "cpp": "c++",
    "cplusplus": "c++",
    "csharp": "c#",
    "c-sharp": "c#",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "torch": "pytorch",
    "k8s": "kubernetes",
    "gcp": "google cloud",
    "tf": "tensorflow",
    "tailwindcss": "tailwind",
    "tailwind css": "tailwind",
}

_SEPARATORS_RE = re.compile(r"[\s_.\-]+")

# Alias lookup on separator-squashed keys so spelling variants
# ("Fast Api", "fast_api", "React.js", "reactjs") canonicalize together.
_SQUASHED_ALIASES = {
    _SEPARATORS_RE.sub("", key): value for key, value in SKILL_ALIASES.items()
}


def canonical_skill_name(name: str) -> str:
    """Canonical comparison key: lowercase, separators removed, aliases resolved."""
    key = _SEPARATORS_RE.sub("", (name or "").strip().lower())
    return _SQUASHED_ALIASES.get(key, key)


def normalize_skill_name(name: str) -> str:
    """Backwards-compatible alias: canonical comparison key for a skill name."""
    return canonical_skill_name(name)


class MatchingService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        embedding_service: EmbeddingService,
    ):
        self.db = db
        self.settings = settings
        self.embedding_service = embedding_service
        self.profile_repo = ProfileRepository(db)
        self.team_project_repo = TeamProjectRepository(db)

    def get_recommendations(
        self, user_id: int, limit: int, q: str | None = None
    ) -> RecommendationListResponse:
        ttl = self.settings.RECOMMENDATION_CACHE_TTL_SECONDS
        query_key = (q or "").strip().lower()
        cache_key = (
            f"recs:{user_id}:{limit}:{query_key}:"
            f"{result_cache.version(result_cache.user_scope(user_id))}"
        )
        cached = result_cache.get(cache_key)
        if cached is not None:
            return cached

        own_profile = self.profile_repo.get_by_user_id(user_id)
        if own_profile is None or own_profile.embedding is None:
            return RecommendationListResponse(
                recommendations=[], total_candidates=0
            )

        candidates = self.profile_repo.list_with_embeddings(
            exclude_user_id=user_id
        )
        if query_key:
            candidates = [
                c for c in candidates if self._candidate_matches_query(c, query_key)
            ]
        if not candidates:
            return RecommendationListResponse(
                recommendations=[], total_candidates=0
            )

        own_skills = {
            normalize_skill_name(user_skill.skill.name)
            for user_skill in self.profile_repo.get_user_skills(user_id)
            if user_skill.skill and user_skill.skill.name
        }
        own_embedding = own_profile.embedding

        scored: list[tuple[float, DeveloperProfile]] = []
        for candidate in candidates:
            score = self._compute_score(
                own_profile, own_skills, own_embedding, candidate
            )
            scored.append((score, candidate))

        scored.sort(key=lambda item: item[0], reverse=True)

        recommendations = [
            self._to_recommendation(score, own_skills, candidate)
            for score, candidate in scored[:limit]
        ]

        response = RecommendationListResponse(
            recommendations=recommendations,
            total_candidates=len(candidates),
        )
        result_cache.set(cache_key, response, ttl)
        return response

    def _compute_score(
        self,
        own_profile: DeveloperProfile,
        own_skills: set[str],
        own_embedding: list[float],
        candidate: DeveloperProfile,
    ) -> float:
        embedding_similarity = self.embedding_service.cosine_similarity(
            own_embedding, candidate.embedding or []
        )

        candidate_skills = {
            normalize_skill_name(user_skill.skill.name)
            for user_skill in candidate.user.skills
            if user_skill.skill and user_skill.skill.name
        }
        skill_similarity = self._jaccard_similarity(own_skills, candidate_skills)

        experience_similarity = self._experience_compatibility(
            own_profile.experience_level, candidate.experience_level
        )

        return (
            self.settings.MATCHING_EMBEDDING_WEIGHT * embedding_similarity
            + self.settings.MATCHING_SKILL_WEIGHT * skill_similarity
            + self.settings.MATCHING_EXPERIENCE_WEIGHT * experience_similarity
        )

    def _to_recommendation(
        self,
        score: float,
        own_skills: set[str],
        candidate: DeveloperProfile,
    ) -> Recommendation:
        candidate_skills = {
            normalize_skill_name(user_skill.skill.name)
            for user_skill in candidate.user.skills
            if user_skill.skill and user_skill.skill.name
        }
        overlap = sorted(own_skills & candidate_skills)

        return Recommendation(
            user=PublicUserResponse(
                id=candidate.user.id,
                username=candidate.user.username,
            ),
            profile=to_public_profile_response(candidate),
            similarity_score=round(score, 4),
            skill_overlap=overlap,
        )

    def _jaccard_similarity(self, a: set[str], b: set[str]) -> float:
        union = a | b
        if not union:
            return 0.0
        return len(a & b) / len(union)

    @staticmethod
    def _candidate_matches_query(candidate: DeveloperProfile, query: str) -> bool:
        """Free-text teammate search across identity + skills + projects."""
        haystacks = [
            (candidate.user.username or "").lower(),
            (candidate.full_name or "").lower(),
            (candidate.college or "").lower(),
            (candidate.location or "").lower(),
        ]
        for user_skill in candidate.user.skills:
            if user_skill.skill and user_skill.skill.name:
                haystacks.append(user_skill.skill.name.lower())
        for portfolio_project in candidate.user.projects:
            if portfolio_project.title:
                haystacks.append(portfolio_project.title.lower())
            for link in portfolio_project.skills or []:
                skill = getattr(link, "skill", None)
                if skill is not None and skill.name:
                    haystacks.append(skill.name.lower())
        return any(query in text for text in haystacks)

    def get_project_recommendations(
        self, team_project_id: int, requester_id: int, limit: int
    ) -> ProjectRecommendationListResponse:
        project = self.team_project_repo.get_by_id(team_project_id)
        if project is None:
            raise NotFoundException("Team project not found")
        if project.creator_id != requester_id:
            raise ForbiddenException("Only the project creator can view recommendations")

        ttl = self.settings.RECOMMENDATION_CACHE_TTL_SECONDS
        cache_key = (
            f"teamrecs:{team_project_id}:{limit}:"
            f"{result_cache.version(result_cache.project_scope(team_project_id))}"
        )
        cached = result_cache.get(cache_key)
        if cached is not None:
            return cached

        if project.embedding is None:
            required = self.team_project_repo.get_required_skills(team_project_id)
            project.embedding = self.embedding_service.embed_team_project(
                project, required
            )
            project.embedding_updated_at = datetime.now(timezone.utc)
            self.db.commit()

        required_links = self.team_project_repo.get_required_skills(team_project_id)
        project_skill_names = {link.skill.name for link in required_links}
        project_skill_names |= set(project.tech_stack or [])
        project_norm_to_display = {}
        for name in project_skill_names:
            norm = normalize_skill_name(name)
            project_norm_to_display.setdefault(norm, name)
        project_norms = set(project_norm_to_display.keys())
        project_embedding = project.embedding or []

        member_rows = self.team_project_repo.list_members(team_project_id)
        exclude_ids = {m.user_id for m in member_rows} | {project.creator_id}
        candidates = self.profile_repo.list_with_embeddings_excluding(
            list(exclude_ids)
        )

        if project.require_same_college:
            from app.data.colleges import same_college

            candidates = [
                c
                for c in candidates
                if same_college(
                    c.college,
                    c.college_id,
                    project.college,
                    project.college_id,
                )
            ]

        app_status = self.team_project_repo.application_status_map(team_project_id)
        invite_status = self.team_project_repo.invitation_status_map(team_project_id)

        scored: list[tuple[float, int, DeveloperProfile, dict]] = []
        for candidate in candidates:
            dev_skills: dict[str, tuple[int, float | None]] = {}
            dev_display: dict[str, str] = {}
            for user_skill in candidate.user.skills:
                norm = normalize_skill_name(user_skill.skill.name)
                dev_skills[norm] = (
                    user_skill.proficiency,
                    user_skill.years_experience,
                )
                dev_display.setdefault(norm, user_skill.skill.name)
            # Portfolio proof: which of the dev's own projects use each skill.
            evidence_titles: dict[str, list[str]] = {}
            for portfolio_project in candidate.user.projects:
                for project_skill in portfolio_project.skills or []:
                    skill = getattr(project_skill, "skill", None)
                    if skill is None or not skill.name:
                        continue
                    norm = normalize_skill_name(skill.name)
                    dev_display.setdefault(norm, skill.name)
                    titles = evidence_titles.setdefault(norm, [])
                    if (
                        portfolio_project.title
                        and portfolio_project.title not in titles
                        and len(titles) < 3
                    ):
                        titles.append(portfolio_project.title)

            embedding_similarity = self.embedding_service.cosine_similarity(
                project_embedding, candidate.embedding or []
            )
            dev_all_norms = set(dev_display.keys())
            score = self._project_match_score(
                project_norms, dev_skills, dev_all_norms, embedding_similarity
            )
            stars = self._score_to_stars(score)
            matched_norms = project_norms & dev_all_norms
            overlap = sorted(dev_display[norm] for norm in matched_norms)
            coverage = len(matched_norms) / len(project_norms) if project_norms else 0.0
            missing = sorted(
                project_norm_to_display[norm] for norm in (project_norms - dev_all_norms)
            )
            # "What they add": strongest listed skills outside the requirements.
            bonus_norms = dev_all_norms - project_norms
            bonus = sorted(
                (norm for norm in bonus_norms if norm in dev_skills),
                key=lambda n: (-(dev_skills[n][0] or 3), dev_display[n].lower()),
            ) + sorted(
                (norm for norm in bonus_norms if norm not in dev_skills),
                key=lambda n: dev_display[n].lower(),
            )
            bonus_names = [dev_display[norm] for norm in bonus[:8]]
            evidence = [
                SkillEvidence(
                    skill=dev_display[norm],
                    project_titles=evidence_titles.get(norm, []),
                    listed=norm in dev_skills,
                )
                for norm in sorted(matched_norms)
            ]
            scored.append(
                {
                    "score": score,
                    "stars": stars,
                    "candidate": candidate,
                    "overlap": overlap,
                    "coverage": coverage,
                    "missing": missing,
                    "bonus": bonus_names,
                    "evidence": evidence,
                }
            )

        scored.sort(key=lambda item: item["score"], reverse=True)

        recommendations = []
        for item in scored[:limit]:
            candidate = item["candidate"]
            recommendations.append(
                ProjectRecommendation(
                    user_id=candidate.user.id,
                    username=candidate.user.username,
                    full_name=candidate.full_name,
                    similarity_score=round(item["score"], 4),
                    stars=item["stars"],
                    skill_overlap=item["overlap"],
                    coverage=round(item["coverage"], 4),
                    missing_skills=item["missing"],
                    bonus_skills=item["bonus"],
                    skill_evidence=item["evidence"],
                    application_status=app_status.get(candidate.user_id),
                    invitation_status=invite_status.get(candidate.user_id),
                )
            )

        return_response = ProjectRecommendationListResponse(
            recommendations=recommendations,
            total_candidates=len(candidates),
        )
        result_cache.set(cache_key, return_response, ttl)
        return return_response

    def _project_match_score(
        self,
        project_norms: set[str],
        dev_skills: dict[str, tuple[int, float | None]],
        dev_all_norms: set[str],
        embedding_similarity: float,
    ) -> float:
        if not project_norms:
            return max(0.0, min(1.0, embedding_similarity))

        matched = project_norms & dev_all_norms
        coverage = len(matched) / len(project_norms)

        if matched:
            depths = []
            for name in matched:
                if name in dev_skills:
                    proficiency, years = dev_skills[name]
                    prof_norm = (proficiency or 3) / 5.0
                    years_norm = min(years or 0.0, 8.0) / 8.0
                else:
                    prof_norm = 2 / 5.0
                    years_norm = 0.5 / 8.0
                depths.append((prof_norm + years_norm) / 2.0)
            avg_depth = sum(depths) / len(depths)
        else:
            avg_depth = 0.0

        embedding = max(0.0, min(1.0, embedding_similarity))
        return 0.6 * coverage + 0.2 * avg_depth + 0.2 * embedding

    def _score_to_stars(self, score: float) -> int:
        stars = 1 + int(score * 4 + 0.5)
        return max(1, min(5, stars))

    def _experience_compatibility(
        self,
        a: ExperienceLevel | None,
        b: ExperienceLevel | None,
    ) -> float:
        if a is None or b is None:
            return 0.0
        if a == b:
            return 1.0

        try:
            index_a = _EXPERIENCE_ORDER.index(a)
            index_b = _EXPERIENCE_ORDER.index(b)
        except ValueError:
            return 0.0

        distance = abs(index_a - index_b)
        if distance == 1:
            return 0.6
        if distance == 2:
            return 0.3
        return 0.1
