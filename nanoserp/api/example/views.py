from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED

from nanoserp.api.example.schemas import (
    ExampleRequest,
    ExampleResponse,
)
from nanoserp.api.security import verify_token

router = APIRouter()

# NOTE: Keep the endpoints in alphabetical order for organization!


@router.post("/", status_code=HTTP_201_CREATED, response_model=ExampleResponse)
async def create_linkedin_profile(
    auth: Annotated[None, Depends(verify_token)],
    request: ExampleRequest,
) -> ExampleResponse:
    return ExampleResponse(message=f"Received: {request.data}")
