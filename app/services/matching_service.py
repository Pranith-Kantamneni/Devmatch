from datetime import datetime, timezone

from sqlalchemy.orm import Session

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
        self, user_id: int, limit: int
    ) -> RecommendationListResponse:
        own_profile = self.profile_repo.get_by_user_id(user_id)
        if own_profile is None or own_profile.embedding is None:
            return RecommendationListResponse(
                recommendations=[], total_candidates=0
            )

        candidates = self.profile_repo.list_with_embeddings(
            exclude_user_id=user_id
        )
        if not candidates:
            return RecommendationListResponse(
                recommendations=[], total_candidates=0
            )

        own_skills = {
            user_skill.skill.name
            for user_skill in self.profile_repo.get_user_skills(user_id)
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

        return RecommendationListResponse(
            recommendations=recommendations,
            total_candidates=len(candidates),
        )

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
            user_skill.skill.name for user_skill in candidate.user.skills
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
            user_skill.skill.name for user_skill in candidate.user.skills
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

    def get_project_recommendations(
        self, team_project_id: int, requester_id: int, limit: int
    ) -> ProjectRecommendationListResponse:
        project = self.team_project_repo.get_by_id(team_project_id)
        if project is None:
            raise NotFoundException("Team project not found")
        if project.creator_id != requester_id:
            raise ForbiddenException("Only the project creator can view recommendations")

        if project.embedding is None:
            required = self.team_project_repo.get_required_skills(team_project_id)
            project.embedding = self.embedding_service.embed_team_project(
                project, required
            )
            project.embedding_updated_at = datetime.now(timezone.utc)
            self.db.commit()

        required_names = {
            link.skill.name
            for link in self.team_project_repo.get_required_skills(team_project_id)
        }
        project_embedding = project.embedding or []

        member_rows = self.team_project_repo.list_members(team_project_id)
        exclude_ids = {m.user_id for m in member_rows} | {project.creator_id}
        candidates = self.profile_repo.list_with_embeddings_excluding(
            list(exclude_ids)
        )

        if project.require_same_college:
            wanted = (project.college or "").strip().lower()
            candidates = [
                c
                for c in candidates
                if (c.college or "").strip().lower() == wanted and wanted
            ]

        app_status = self.team_project_repo.application_status_map(team_project_id)
        invite_status = self.team_project_repo.invitation_status_map(team_project_id)

        scored: list[tuple[float, DeveloperProfile]] = []
        for candidate in candidates:
            candidate_skills = {
                user_skill.skill.name for user_skill in candidate.user.skills
            }
            embedding_similarity = self.embedding_service.cosine_similarity(
                project_embedding, candidate.embedding or []
            )
            skill_similarity = self._jaccard_similarity(
                required_names, candidate_skills
            )
            weight_sum = (
                self.settings.MATCHING_EMBEDDING_WEIGHT
                + self.settings.MATCHING_SKILL_WEIGHT
            ) or 1.0
            score = (
                self.settings.MATCHING_EMBEDDING_WEIGHT * embedding_similarity
                + self.settings.MATCHING_SKILL_WEIGHT * skill_similarity
            ) / weight_sum
            scored.append((score, candidate))

        scored.sort(key=lambda item: item[0], reverse=True)

        recommendations = []
        for score, candidate in scored[:limit]:
            candidate_skills = {
                user_skill.skill.name for user_skill in candidate.user.skills
            }
            recommendations.append(
                ProjectRecommendation(
                    user_id=candidate.user.id,
                    username=candidate.user.username,
                    full_name=candidate.full_name,
                    similarity_score=round(score, 4),
                    skill_overlap=sorted(required_names & candidate_skills),
                    application_status=app_status.get(candidate.user_id),
                    invitation_status=invite_status.get(candidate.user_id),
                )
            )

        return ProjectRecommendationListResponse(
            recommendations=recommendations,
            total_candidates=len(candidates),
        )

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
