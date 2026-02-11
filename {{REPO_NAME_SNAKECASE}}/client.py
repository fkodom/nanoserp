import logging
from functools import wraps
from typing import Callable, Coroutine

import httpx

from {{REPO_NAME_SNAKECASE}}.api.example.schemas import (
    ExampleRequest,
    ExampleResponse,
)
from {{REPO_NAME_SNAKECASE}}.exceptions import (
    APIError,
    AuthenticationError,
    InternalError,
    NotAcceptableError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
)
from {{REPO_NAME_SNAKECASE}}.settings import AuthSettings

logger = logging.getLogger(__name__)


def handle_api_errors(fn: Callable[..., Coroutine]):
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            raise parse_error_response(e.response) from e
        except httpx.RequestError as e:
            # Network-related errors (DNS failure, refused connection, etc)
            raise ServiceUnavailableError("Service is currently unavailable") from e

    return wrapper


def parse_error_response(response: httpx.Response) -> APIError:
    try:
        # Errors originating from this API have the following structure:
        #     {"error": {"message": "error message"}}
        # If the response is not in this format, treat it as a generic 500 error.
        response_json: dict = response.json()
        error: dict | None = response_json.get("error", None)
        if not isinstance(error, dict):
            logger.error(f"An unknown error occurred: {response.text}")
            return InternalError("An unknown error occurred")

        message = error.get("message", None)
        if response.status_code == 401:
            return AuthenticationError(message=message)
        elif response.status_code == 404:
            return NotFoundError(message=message)
        elif response.status_code == 406:
            return NotAcceptableError(message=message)
        elif response.status_code == 429:
            return RateLimitError(message=message)
        elif response.status_code == 503:
            return ServiceUnavailableError(message=message)
        else:
            return InternalError(message=message)  # 500

    # Catch any exceptions that occur while parsing the error response.  Essentially,
    # any error type that we don't handle successfully will be treated as a 500 error
    # with a generic message, and the error stack trace will be logged for debugging.
    except Exception as e:
        logger.error(f"Failed to parse error response: {response.text}", exc_info=e)
        return InternalError("An unknown error occurred")  # 500


class AsyncClient:
    def __init__(self, base_url: str, api_key: str | None = None):
        if api_key is None:
            api_key = AuthSettings().API_KEY
        self.httpx_client = httpx.AsyncClient(
            base_url=base_url, headers={"Authorization": f"Bearer {api_key}"}
        )

    @handle_api_errors
    async def is_healthy(self) -> bool:
        response = await self.httpx_client.get("/health")
        response.raise_for_status()
        return True

    # Submodule for the 'example' routes
    # NOTE: Consider breaking the client out into submodules, if the number of client-
    # facing routes becomes too large (i.e. if this file becomes too long/complex).

    async def create_example(self, data: str) -> str:
        response = await self.httpx_client.post(
            "/api/v1/examples", json=ExampleRequest(data=data).model_dump()
        )
        response.raise_for_status()
        return ExampleResponse(**response.json()).message
