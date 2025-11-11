import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class ProcessTimeMiddleware(BaseHTTPMiddleware):  # pylint: disable=too-few-public-methods
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # url = request.url.path
        # if request.query_params:
        #     url += f"?{request.query_params}"
        start_time = time.perf_counter()
        response = await call_next(request)
        end_time = time.perf_counter()
        process_time = end_time - start_time
        # host = getattr(getattr(request, "client", None), "host", None)
        # port = getattr(getattr(request, "client", None), "port", None)
        response.headers["X-Process-Time"] = f"{process_time:.2f}"
        return response
