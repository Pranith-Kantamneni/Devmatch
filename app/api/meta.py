from fastapi import APIRouter, Query

from app.data.branches import BRANCHES
from app.data.colleges import COLLEGES, get_college, search_colleges
from app.schemas.meta import BranchListResponse, CollegeListResponse, CollegeOption

router = APIRouter(prefix="/meta", tags=["Metadata"])


@router.get(
    "/colleges",
    response_model=CollegeListResponse,
    summary="Search the canonical college directory",
)
def list_colleges(
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=8, ge=1, le=20),
):
    if not q or not q.strip():
        # Curated first page: flagship campuses across regions.
        featured_ids = [
            "iit-bombay",
            "iit-delhi",
            "iit-madras",
            "nit-trichy",
            "bits-pilani",
            "vit-vellore",
            "iiit-hyderabad",
            "dtu-delhi",
        ]
        results = [get_college(cid) for cid in featured_ids]
        results = [r for r in results if r is not None]
    else:
        results = search_colleges(q, limit)
    return CollegeListResponse(
        colleges=[CollegeOption(**entry) for entry in results],
        total=len(COLLEGES),
    )


@router.get(
    "/branches",
    response_model=BranchListResponse,
    summary="List canonical branch / department options",
)
def list_branches():
    return BranchListResponse(branches=list(BRANCHES), total=len(BRANCHES))
