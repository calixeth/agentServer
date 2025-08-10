import trace

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from common.tracing import Otel


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        tid = Otel.get_tid()
        if tid:
            response.headers["X-Trace-Id"] = tid

        return response
