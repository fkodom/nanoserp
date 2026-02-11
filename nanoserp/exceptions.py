"""
Generic exception types for the 'nanoserp' library.  It is strongly encouraged
to derive custom exception types for other parts of the codebase, so that we get
clearer error messages.

NOTE: For readability, please sort in ascending order by status code. :)
"""

from typing import Literal, Optional


class NanoserpError(Exception):
    """Base class for all custom exceptions in the 'nanoserp' library."""

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message


class AuthenticationError(NanoserpError):
    """Generic error for auth-related issues. E.g. invalid API key or expired token."""

    name: Literal["authentication_error"] = "authentication_error"
    status_code: Literal[401] = 401


class ForbiddenError(NanoserpError):
    """Generic error for when a request is made to a resource that the user is not
    authorized to access.  This is a catch-all for any 403 errors.
    """

    name: Literal["forbidden_error"] = "forbidden_error"
    status_code: Literal[403] = 403


class NotFoundError(NanoserpError):
    """Generic error for when a requested resource is not found.  This is a catch-all for
    any 404 errors.
    """

    name: Literal["not_found_error"] = "not_found_error"
    status_code: Literal[404] = 404


class NotAcceptableError(NanoserpError):
    """Generic error for when a request is invalid because the server cannot produce a
    response that is acceptable.  This could be because of the request's Accept headers,
    or because the request contains impermissible (but otherwise valid) parameters, such
    as adversarial text inputs.
    """

    name: Literal["not_acceptable_error"] = "not_acceptable_error"
    status_code: Literal[406] = 406


class ConflictError(NanoserpError):
    """Generic error for when a request is made to create a new resource, but another
    resource with the same ID (or other unique constraint) already exists.
    """

    name: Literal["conflict_error"] = "conflict_error"
    status_code: Literal[409] = 409


class ContentTooLargeError(NanoserpError):
    """Generic error for when a request's payload is too large for the server to process.
    This is a catch-all for any 413 errors.
    """

    name: Literal["payload_too_large_error"] = "payload_too_large_error"
    status_code: Literal[413] = 413


class UnprocessableEntityError(NanoserpError):
    """Generic error for when a request is valid, but the server cannot process it.  This
    is a catch-all for any 422 errors.
    """

    name: Literal["unprocessable_entity_error"] = "unprocessable_entity_error"
    status_code: Literal[422] = 422


class RateLimitError(NanoserpError):
    """Generic error for rate limiting -- both for 'nanoserp' client rate limits,
    and for rate limits on any downstream services (e.g. OpenAI).
    """

    name: Literal["rate_limit_error"] = "rate_limit_error"
    status_code: Literal[429] = 429


class InternalError(NanoserpError):
    """Generic error for internal server errors.  This is a catch-all for any
    unexpected errors that occur on the server side.
    """

    name: Literal["internal_error"] = "internal_error"
    status_code: Literal[500] = 500


class ServiceUnavailableError(NanoserpError):
    """Generic error for when the service is unavailable.  This could be due
    to an internal error, or because an external service is also down (e.g. OpenAI).
    """

    name: Literal["service_unavailable_error"] = "service_unavailable_error"
    status_code: Literal[503] = 503
