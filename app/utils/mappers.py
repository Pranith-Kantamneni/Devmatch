from app.db.models.profile import DeveloperProfile
from app.schemas.profile import (
    ProfileResponse,
    ProjectResponse,
    PublicProfileResponse,
)
from app.schemas.skill import SkillBrief, UserSkillResponse


def to_user_skill_responses(profile: DeveloperProfile) -> list[UserSkillResponse]:
    return [
        UserSkillResponse(
            skill_id=user_skill.skill.id,
            name=user_skill.skill.name,
            category=user_skill.skill.category,
            proficiency=user_skill.proficiency,
            years_experience=user_skill.years_experience,
        )
        for user_skill in profile.user.skills
    ]


def to_project_responses(profile: DeveloperProfile) -> list[ProjectResponse]:
    return [
        ProjectResponse(
            id=project.id,
            title=project.title,
            description=project.description,
            url=project.url,
            skills=[
                SkillBrief(
                    id=project_skill.skill.id,
                    name=project_skill.skill.name,
                    category=project_skill.skill.category,
                )
                for project_skill in project.skills
            ],
        )
        for project in profile.user.projects
    ]


def to_profile_response(profile: DeveloperProfile) -> ProfileResponse:
    return ProfileResponse(
        user_id=profile.user_id,
        full_name=profile.full_name,
        bio=profile.bio,
        location=profile.location,
        education=profile.education,
        college=profile.college,
        experience_level=profile.experience_level,
        github_url=profile.github_url,
        linkedin_url=profile.linkedin_url,
        portfolio_url=profile.portfolio_url,
        availability=profile.availability,
        collaboration_preferences=profile.collaboration_preferences,
        skills=to_user_skill_responses(profile),
        projects=to_project_responses(profile),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def to_public_profile_response(profile: DeveloperProfile) -> PublicProfileResponse:
    return PublicProfileResponse(
        user_id=profile.user_id,
        full_name=profile.full_name,
        bio=profile.bio,
        location=profile.location,
        education=profile.education,
        college=profile.college,
        experience_level=profile.experience_level,
        github_url=profile.github_url,
        linkedin_url=profile.linkedin_url,
        portfolio_url=profile.portfolio_url,
        availability=profile.availability,
        collaboration_preferences=profile.collaboration_preferences,
        skills=to_user_skill_responses(profile),
        projects=to_project_responses(profile),
    )
