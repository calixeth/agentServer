import logging

from fastapi import APIRouter
from starlette.responses import Response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    return Response(status_code=204)  # 204 No Content


@router.get("/")
async def root():
    """Root endpoint that returns service status"""
    return "UP"


@router.get("/api/health")
async def health():
    """Health check endpoint"""
    return "UP"
