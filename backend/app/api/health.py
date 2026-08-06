from fastapi import APIRouter

from app.core.constants import APP_VERSION
from app.schemas.response import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="healthy", version=APP_VERSION)
