# TODO:
# - Add visibility metrics with logfire

import logging
from typing import Literal

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from nanoserp.api.example.views import router as example_router
from nanoserp.exceptions import APIError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

v1_router = APIRouter()
# NOTE: Add API routers in alphabetical order for organization!  For example:
v1_router.include_router(example_router, prefix="/examples", tags=["examples"])

app = FastAPI()
app.include_router(v1_router, prefix="/api/v1")
app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """A generic error handler for all custom exceptions in 'nanoserp'. If any
    other, targeted error handlers are needed, please add them *above* this method.
    FastAPI will use the first matching error handler it finds, so order matters.
    """
    return JSONResponse(
        status_code=getattr(exc, "status_code", 500),
        content={
            "error": {
                "message": exc.message,
                "type": getattr(exc, "name", "APIError"),
            }
        },
    )


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


@app.get("/health", response_model=HealthResponse, status_code=200)
async def health():
    return HealthResponse()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
