from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.applications import Starlette


async def homepage(request: Request) -> HTMLResponse:
    return HTMLResponse('')


async def upload(request: Request) -> HTMLResponse:
    return HTMLResponse('')


routes = [
    Route('/', endpoint=homepage, methods=['GET']),
    Route('/upload', endpoint=upload, methods=['POST']),
]

app = Starlette(routes=routes)
