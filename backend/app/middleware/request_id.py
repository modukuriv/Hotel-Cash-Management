from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.services.logging import new_request_id, set_request_id


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id") or new_request_id()
        set_request_id(request_id)
        response: Response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response
