from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_db
from app.schemas.oauth import OAuthLoginData, OAuthProviderStatus
from app.schemas.user import Token
from app.services.oauth_service import OAuthService

router = APIRouter(prefix="/auth/oauth", tags=["OAuth"])


def get_oauth_service(db: Session = Depends(get_db)) -> OAuthService:
    return OAuthService(db, get_settings())


@router.get(
    "/providers",
    response_model=list[OAuthProviderStatus],
    summary="List social login providers and whether each is enabled",
)
def list_providers(service: OAuthService = Depends(get_oauth_service)):
    return service.configured_providers()


@router.get(
    "/{provider}/login",
    response_model=OAuthLoginData,
    summary="Start social login: get the provider authorization URL",
)
def oauth_login(provider: str, service: OAuthService = Depends(get_oauth_service)):
    return service.get_login_data(provider)


@router.get(
    "/{provider}/callback",
    response_model=Token,
    summary="Complete social login and receive a JWT access token",
)
def oauth_callback(
    provider: str,
    code: str = Query(..., min_length=1),
    state: str = Query(..., min_length=1),
    service: OAuthService = Depends(get_oauth_service),
):
    return service.handle_callback(provider, code, state)
