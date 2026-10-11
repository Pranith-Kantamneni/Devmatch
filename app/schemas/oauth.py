from pydantic import BaseModel


class OAuthProviderStatus(BaseModel):
    provider: str
    enabled: bool


class OAuthLoginData(BaseModel):
    authorization_url: str
    state: str
