import secrets
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from {{REPO_NAME_SNAKECASE}}.exceptions import AuthenticationError
from {{REPO_NAME_SNAKECASE}}.settings import AuthSettings

security = HTTPBearer()


async def verify_token(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> None:
    settings = AuthSettings()
    if (settings.API_KEY is not None) and (
        not secrets.compare_digest(token.credentials, settings.API_KEY)
    ):
        # If an API key is set, use it for authentication
        # This is a special case for API key authentication
        # and does not require JWT verification.
        raise AuthenticationError("Invalid API key")
