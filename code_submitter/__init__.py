from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.applications import Starlette


async def homepage(request: Request) -> HTMLResponse:
    return HTMLResponse('')

routes = [
    Route('/', endpoint=homepage),
]

app = Starlette(routes=routes)
