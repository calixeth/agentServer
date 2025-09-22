import logging
import time
from typing import Optional

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from common.error_messages import get_error_message
from common.exceptions import ErrorCode
from common.response import RestResponse
from config import SETTINGS
from utils.jwt_utils import verify_token

security = HTTPBearer()
logger = logging.getLogger(__name__)


class AuthConfig:
    """Authentication configuration"""
    PUBLIC_PREFIXES = [
        "/api/health",
        "/openapi.json",
        "/api/auth",
        "/api/digital_human/list",
        "/api/digital_human/get_by_id",
        "/api/x/user",
        "/api/twitter-tts/tasks",
        "/api/callback",
    ]


class AuthResponse:
    """Authentication response helper"""

    @staticmethod
    def error(error_code: ErrorCode) -> JSONResponse:
        return JSONResponse(
            status_code=200,
            content=RestResponse(
                code=error_code,
                msg=get_error_message(error_code)
            ).model_dump(exclude_none=True)
        )


class AuthError(Exception):
    def __init__(self, error_code: ErrorCode):
        self.error_code = error_code


class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path

        # Check public paths
        if any(path.startswith(prefix) for prefix in AuthConfig.PUBLIC_PREFIXES):
            return await call_next(request)

        try:
            # Try JWT authentication
            await self._authenticate_jwt(request)
            return await call_next(request)
        except AuthError as e:
            return AuthResponse.error(e.error_code)

    async def _authenticate_jwt(self, request: Request):
        """Authenticate using JWT token"""
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise AuthError(ErrorCode.TOKEN_MISSING)

            token = auth_header.split(" ")[1] if auth_header.startswith("Bearer ") else auth_header
            if SETTINGS.TEST_TOKEN and SETTINGS.TEST_TOKEN == token:
                payload = {
                    "username": "test",
                    "wallet_address": "test",
                    "tenant_id": "test",
                }
            else:
                payload = verify_token(token)
            if not payload:
                raise AuthError(ErrorCode.TOKEN_EXPIRED)

            request.state.user = payload
        except (IndexError, AttributeError) as e:
            logger.error(f"JWT token parsing error: {str(e)}")
            raise AuthError(ErrorCode.TOKEN_INVALID)

    def _verify_timestamp(self, timestamp: str, max_age: int = 300) -> bool:
        """Verify if timestamp is within allowed range"""
        try:
            current_time = int(time.time())
            request_time = int(timestamp)
            return abs(current_time - request_time) <= max_age
        except ValueError:
            return False


async def get_current_user(request: Request) -> dict:
    """Get authenticated user from request"""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=401,
            detail=get_error_message(ErrorCode.UNAUTHORIZED)
        )
    return user


async def get_optional_current_user(request: Request) -> Optional[dict]:
    """Get optional user from request"""
    return getattr(request.state, "user", None)
