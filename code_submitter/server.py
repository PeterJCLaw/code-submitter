import io
import zipfile

import databases
from sqlalchemy.sql import select
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from starlette.middleware import Middleware
from starlette.templating import Jinja2Templates
from starlette.applications import Starlette
from starlette.authentication import requires
from starlette.datastructures import UploadFile
from starlette.middleware.authentication import AuthenticationMiddleware

from . import auth, config
from .auth import User
from .tables import Archive, ChoiceHistory

database = databases.Database(config.DATABASE_URL, force_rollback=config.TESTING)
templates = Jinja2Templates(directory='templates')


@requires('authenticated')
async def homepage(request: Request) -> Response:
    chosen = await database.fetch_one(
        select([ChoiceHistory]).select_from(
            ChoiceHistory.join(Archive),
        ).where(
            Archive.c.team == request.user.team,
        ).order_by(
            ChoiceHistory.c.created.desc(),
        ),
    )
    uploads = await database.fetch_all(
        select(
            [
                Archive.c.id,
                Archive.c.username,
                Archive.c.team,
                # omit content which is probably large and we don't need
                Archive.c.created,
            ],
        ).where(
            Archive.c.username == request.user.username or
            Archive.c.team == request.user.team,
        ).order_by(
            Archive.c.created.desc(),
        ),
    )
    return templates.TemplateResponse('index.html', {
        'request': request,
        'chosen': chosen,
        'uploads': uploads,
    })


@requires('authenticated')
@database.transaction()
async def upload(request: Request) -> Response:
    user: User = request.user

    if not user.team:
        return Response(
            "Must be a member of a team to be able to upload files",
            status_code=403,
        )

    form = await request.form()
    archive = form['archive']

    if not isinstance(archive, UploadFile):
        return Response("Must upload a file", status_code=400)

    if archive.content_type not in ('application/zip', 'application/x-zip-compressed'):
        return Response(
            "Must upload a ZIP file, not {!r}".format(archive.content_type),
            status_code=400,
        )

    contents = await archive.read()
    if isinstance(contents, str):
        raise ValueError(
            "Uploaded files should always be bytes (not str). "
            "Why doesn't starlette enforce this?",
        )

    try:
        zf = zipfile.ZipFile(io.BytesIO(contents))
    except zipfile.BadZipFile:
        return Response("Must upload a ZIP file", status_code=400)

    try:
        zf.getinfo('robot.py')
    except KeyError:
        return Response(
            "ZIP file must contain a 'robot.py' at the root",
            status_code=400,
        )

    archive_id = await database.execute(
        Archive.insert().values(
            content=contents,
            username=request.user.username,
            team=request.user.team,
        ),
    )
    if form.get('choose'):
        await database.execute(
            ChoiceHistory.insert().values(
                archive_id=archive_id,
                username=request.user.username,
            ),
        )

    return RedirectResponse(
        request.url_for('homepage'),
        # 302 so that the browser switches to GET
        status_code=302,
    )

routes = [
    Route('/', endpoint=homepage, methods=['GET']),
    Route('/upload', endpoint=upload, methods=['POST']),
]

middleware = [
    Middleware(
        AuthenticationMiddleware,
        backend=config.get_auth_backend(),
        on_error=auth.auth_required_response,
    ),
]

app = Starlette(
    routes=routes,
    on_startup=[database.connect],
    on_shutdown=[database.disconnect],
    middleware=middleware,
)
