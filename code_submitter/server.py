from __future__ import annotations

import io
import zipfile
import datetime

import databases
from sqlalchemy.sql import and_, select
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import Response, JSONResponse, RedirectResponse
from starlette.middleware import Middleware
from starlette.templating import Jinja2Templates
from starlette.applications import Starlette
from starlette.authentication import requires
from starlette.datastructures import UploadFile
from starlette.middleware.authentication import AuthenticationMiddleware

from . import auth, utils, config
from .auth import User, BLUESHIRT_SCOPE
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

    if BLUESHIRT_SCOPE in request.auth.scopes:
        teams_submissions = await utils.get_chosen_submissions_info(database)
    else:
        teams_submissions = ()

    return templates.TemplateResponse('index.html', {
        'request': request,
        'chosen': chosen,
        'uploads': uploads,
        'teams_submissions': teams_submissions,
        'BLUESHIRT_SCOPE': BLUESHIRT_SCOPE,
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
            f"Must upload a ZIP file, not {archive.content_type!r}",
            status_code=400,
        )

    contents = await archive.read()

    try:
        zf = zipfile.ZipFile(io.BytesIO(contents))
    except zipfile.BadZipFile:
        return Response("Must upload a ZIP file", status_code=400)

    for filepath in config.REQUIRED_FILES_IN_ARCHIVE:
        try:
            zf.getinfo(filepath)
        except KeyError:
            return Response(
                f"ZIP file must contain a file named exactly {filepath!r}.\n"
                "Found the following files:\n " +
                "\n ".join(zf.namelist()),
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


@requires('authenticated')
async def archive(request: Request) -> Response:
    user: User = request.user
    if not user.team:
        return Response(
            "Must be a member of a team to be able to download individual archives",
            status_code=403,
        )

    archive_id = request.path_params['archive_id']

    archive = await database.fetch_one(
        select([
            Archive.c.content,
        ]).where(and_(
            Archive.c.id == archive_id,
            Archive.c.team == user.team,
        )),
    )

    if archive is None:
        return Response(
            f"{archive_id!r} is not a valid archive id",
            status_code=404,
        )

    filename = f'upload-{archive_id}.zip'

    return Response(
        archive['content'],
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        media_type='application/zip',
    )


@requires(['authenticated', BLUESHIRT_SCOPE])
async def download_submissions(request: Request) -> Response:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode='w') as zf:
        await utils.collect_submissions(database, zf)

    filename = 'submissions-{now}.zip'.format(
        now=datetime.datetime.now(datetime.timezone.utc),
    )

    return Response(
        buffer.getvalue(),
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        media_type='application/zip',
    )


async def health_check(request: Request) -> Response:
    return JSONResponse({
        # By definition the server is OK if we get here.
        'server': 'ok',
    })


routes = [
    Route('/', endpoint=homepage, methods=['GET']),
    Route('/upload', endpoint=upload, methods=['POST']),
    Route('/archive/{archive_id:int}', endpoint=archive, methods=['GET']),
    Route('/download-submissions', endpoint=download_submissions, methods=['GET']),
    Route('/health-check', endpoint=health_check, methods=['GET']),
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
