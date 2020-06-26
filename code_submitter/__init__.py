import io
import zipfile

from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates
from starlette.applications import Starlette
from starlette.datastructures import UploadFile

templates = Jinja2Templates(directory='templates')


async def homepage(request: Request) -> Response:
    return templates.TemplateResponse('index.html', {'request': request})


async def upload(request: Request) -> Response:
    form = await request.form()
    archive = form['archive']

    if not isinstance(archive, UploadFile):
        return Response("Must upload a file", status_code=400)

    if archive.content_type != 'application/zip':
        return Response("Must upload a ZIP file", status_code=400)

    contents = await archive.read()
    if isinstance(contents, str):
        raise ValueError(
            "Uploaded files should always be bytes (not str). "
            "Why doesn't starlette enforce this?",
        )

    try:
        zipfile.ZipFile(io.BytesIO(contents))
    except zipfile.BadZipFile:
        return Response("Must upload a ZIP file", status_code=400)

    return Response('')


routes = [
    Route('/', endpoint=homepage, methods=['GET']),
    Route('/upload', endpoint=upload, methods=['POST']),
]

app = Starlette(routes=routes)
