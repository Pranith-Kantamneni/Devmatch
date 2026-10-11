"""Social login via Google, GitHub, and LinkedIn (OAuth 2.0 authorization code flow).

Flow:
  1. Frontend calls GET /auth/oauth/{provider}/login → receives
     {authorization_url, state}. The browser is redirected to the provider.
  2. The provider redirects back to the configured redirect URI with
     ?code=... The frontend extracts the code and calls
     GET /auth/oauth/{provider}/callback?code=...&state=...
  3. The backend verifies state (CSRF), exchanges the code for an access
     token, fetches the provider profile, finds or creates the local user,
     and returns the standard JWT Token.

No new third-party dependencies: HTTP is done with httpx (already required).
"""

import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx
import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import (
    AppException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.db.models.oauth_account import OAuthAccount
from app.db.models.profile import DeveloperProfile
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import Token


SUPPORTED_PROVIDERS = ("google", "github", "linkedin")


@dataclass(frozen=True)
class ProviderConfig:
    authorize_url: str
    token_url: str
    scopes: tuple[str, ...]


PROVIDER_CONFIGS: dict[str, ProviderConfig] = {
    "google": ProviderConfig(
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        scopes=("openid", "email", "profile"),
    ),
    "github": ProviderConfig(
        authorize_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        scopes=("read:user", "user:email"),
    ),
    "linkedin": ProviderConfig(
        authorize_url="https://www.linkedin.com/oauth/v2/authorization",
        token_url="https://www.linkedin.com/oauth/v2/accessToken",
        scopes=("openid", "profile", "email"),
    ),
}


@dataclass
class ProviderProfile:
    provider_user_id: str
    email: str | None
    email_verified: bool
    name: str | None
    username_hint: str | None = None


class OAuthNotConfiguredException(AppException):
    status_code = 501
    detail = "OAuth provider is not configured"


class OAuthService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.user_repo = UserRepository(db)

    # -- provider setup -------------------------------------------------

    def _require_provider(self, provider: str) -> ProviderConfig:
        if provider not in SUPPORTED_PROVIDERS:
            raise NotFoundException(f"Unsupported OAuth provider '{provider}'")
        client_id, client_secret, redirect_uri = self._credentials(provider)
        if not client_id or not client_secret or not redirect_uri:
            raise OAuthNotConfiguredException(
                f"OAuth provider '{provider}' is not configured on this server"
            )
        return PROVIDER_CONFIGS[provider]

    def _credentials(self, provider: str) -> tuple[str | None, str | None, str | None]:
        prefix = provider.upper()
        return (
            getattr(self.settings, f"{prefix}_CLIENT_ID", None),
            getattr(self.settings, f"{prefix}_CLIENT_SECRET", None),
            getattr(self.settings, f"{prefix}_REDIRECT_URI", None),
        )

    def configured_providers(self) -> list[dict]:
        result = []
        for provider in SUPPORTED_PROVIDERS:
            client_id, client_secret, redirect_uri = self._credentials(provider)
            result.append(
                {
                    "provider": provider,
                    "enabled": bool(client_id and client_secret and redirect_uri),
                }
            )
        return result

    # -- state (CSRF protection) ----------------------------------------

    def create_state(self, provider: str) -> str:
        self._require_provider(provider)
        now = datetime.now(timezone.utc)
        payload = {
            "type": "oauth_state",
            "provider": provider,
            "nonce": secrets.token_urlsafe(24),
            "iat": now,
            "exp": now
            + timedelta(minutes=self.settings.OAUTH_STATE_EXPIRE_MINUTES),
        }
        return jwt.encode(
            payload,
            self.settings.JWT_SECRET_KEY,
            algorithm=self.settings.JWT_ALGORITHM,
        )

    def verify_state(self, state: str, provider: str) -> None:
        try:
            payload = jwt.decode(
                state,
                self.settings.JWT_SECRET_KEY,
                algorithms=[self.settings.JWT_ALGORITHM],
            )
        except jwt.ExpiredSignatureError:
            raise ForbiddenException("OAuth session expired. Please try again.")
        except jwt.InvalidTokenError:
            raise ForbiddenException("Invalid OAuth state. Please try again.")
        if payload.get("type") != "oauth_state" or payload.get("provider") != provider:
            raise ForbiddenException("Invalid OAuth state. Please try again.")

    # -- authorization redirect ------------------------------------------

    def get_login_data(self, provider: str) -> dict:
        from urllib.parse import urlencode

        config = self._require_provider(provider)
        client_id, _, redirect_uri = self._credentials(provider)
        state = self.create_state(provider)
        params = urlencode(
            {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": " ".join(config.scopes),
                "state": state,
            }
        )
        return {
            "authorization_url": f"{config.authorize_url}?{params}",
            "state": state,
        }

    # -- code exchange + profile -----------------------------------------

    def exchange_code(self, provider: str, code: str) -> str:
        config = self._require_provider(provider)
        client_id, client_secret, redirect_uri = self._credentials(provider)
        try:
            response = httpx.post(
                config.token_url,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ValidationException(
                f"Failed to complete {provider} login. Please try again."
            ) from exc
        access_token = data.get("access_token")
        if not access_token:
            raise ValidationException(
                f"Failed to complete {provider} login. Please try again."
            )
        return access_token

    def fetch_profile(self, provider: str, access_token: str) -> ProviderProfile:
        try:
            if provider == "google":
                return self._fetch_google_profile(access_token)
            if provider == "github":
                return self._fetch_github_profile(access_token)
            return self._fetch_linkedin_profile(access_token)
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            raise ValidationException(
                f"Failed to fetch {provider} profile. Please try again."
            ) from exc

    def _fetch_google_profile(self, access_token: str) -> ProviderProfile:
        response = httpx.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()
        return ProviderProfile(
            provider_user_id=str(data["sub"]),
            email=data.get("email"),
            email_verified=bool(data.get("email_verified", False)),
            name=data.get("name"),
            username_hint=data.get("given_name") or data.get("name"),
        )

    def _fetch_github_profile(self, access_token: str) -> ProviderProfile:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }
        response = httpx.get("https://api.github.com/user", headers=headers, timeout=15.0)
        response.raise_for_status()
        data = response.json()
        email = data.get("email")
        verified = bool(email)
        if not email:
            # Private emails require the dedicated emails endpoint.
            emails_resp = httpx.get(
                "https://api.github.com/user/emails", headers=headers, timeout=15.0
            )
            emails_resp.raise_for_status()
            for entry in emails_resp.json():
                if entry.get("primary") and entry.get("verified"):
                    email = entry.get("email")
                    verified = True
                    break
        return ProviderProfile(
            provider_user_id=str(data["id"]),
            email=email,
            email_verified=verified,
            name=data.get("name"),
            username_hint=data.get("login"),
        )

    def _fetch_linkedin_profile(self, access_token: str) -> ProviderProfile:
        response = httpx.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()
        return ProviderProfile(
            provider_user_id=str(data["sub"]),
            email=data.get("email"),
            email_verified=bool(data.get("email_verified", False)),
            name=data.get("name"),
            username_hint=data.get("given_name") or data.get("name"),
        )

    # -- find or create ----------------------------------------------------

    def handle_callback(self, provider: str, code: str, state: str) -> Token:
        self._require_provider(provider)
        if not code:
            raise ValidationException("Missing authorization code")
        self.verify_state(state, provider)
        access_token = self.exchange_code(provider, code)
        profile = self.fetch_profile(provider, access_token)
        user = self.find_or_create_user(provider, profile)
        from app.services.auth_service import AuthService

        return AuthService(self.db).create_token_pair(user)

    def find_or_create_user(self, provider: str, profile: ProviderProfile) -> User:
        if not profile.provider_user_id:
            raise ValidationException(
                f"Could not identify your {provider} account. Please try again."
            )

        existing_link = (
            self.db.query(OAuthAccount)
            .filter(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == profile.provider_user_id,
            )
            .first()
        )
        if existing_link is not None:
            user = self.user_repo.get_by_id(existing_link.user_id)
            if user is None:
                raise ValidationException("Account no longer exists")
            return user

        email = (profile.email or "").strip().lower() or None
        if email is None or not profile.email_verified:
            raise ValidationException(
                f"No verified email found on your {provider} account. "
                "Please verify your email with the provider and try again."
            )

        user = self.user_repo.get_by_email(email)
        if user is None:
            user = self._create_oauth_user(email, profile)
        self._link_account(user.id, provider, profile, email)
        return user

    def _link_account(
        self, user_id: int, provider: str, profile: ProviderProfile, email: str | None
    ) -> OAuthAccount:
        link = OAuthAccount(
            user_id=user_id,
            provider=provider,
            provider_user_id=profile.provider_user_id,
            email=email,
        )
        try:
            self.db.add(link)
            self.db.commit()
            self.db.refresh(link)
            return link
        except IntegrityError:
            self.db.rollback()
            # Lost a race (parallel callbacks) — reuse the winning row.
            existing = (
                self.db.query(OAuthAccount)
                .filter(
                    OAuthAccount.provider == provider,
                    OAuthAccount.provider_user_id == profile.provider_user_id,
                )
                .first()
            )
            if existing is not None:
                return existing
            raise ConflictException("This social account is already linked")

    def _create_oauth_user(self, email: str, profile: ProviderProfile) -> User:
        username = self._unique_username(profile.username_hint or profile.name or email)
        user = User(username=username, email=email, password_hash=None)
        try:
            user = self.user_repo.create(user)
        except IntegrityError:
            self.db.rollback()
            # Email was just taken by a concurrent signup — reuse it.
            user = self.user_repo.get_by_email(email)
            if user is None:
                raise ConflictException("Username or email already exists")
            return user
        try:
            self.db.add(DeveloperProfile(user_id=user.id))
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
        return user

    def _unique_username(self, hint: str) -> str:
        base = re.sub(r"[^a-zA-Z0-9_]", "_", (hint or "").strip().lower())
        base = re.sub(r"_+", "_", base).strip("_")
        if "@" in hint and not base:
            base = "user"
        if len(base) < 3:
            base = (base + "_user")[:50]
        base = base[:50]
        username = base
        suffix = 0
        while self.user_repo.get_by_username(username) is not None:
            suffix += 1
            username = f"{base[:44]}_{suffix}"
        return username
