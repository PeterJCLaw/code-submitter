from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates
from starlette.applications import Starlette

templates = Jinja2Templates(directory='templates')


async def homepage(request: Request) -> Response:
    return templates.TemplateResponse('index.html', {'request': request})


async def upload(request: Request) -> Response:
    return Response('')


routes = [
    Route('/', endpoint=homepage, methods=['GET']),
    Route('/upload', endpoint=upload, methods=['POST']),
]

app = Starlette(routes=routes)
