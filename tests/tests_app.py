import io
import asyncio
import zipfile
import tempfile
import unittest
from typing import IO, TypeVar, Awaitable

import alembic  # type: ignore[import]
from sqlalchemy import create_engine
from alembic.config import Config  # type: ignore[import]
from starlette.config import environ
from starlette.testclient import TestClient
from code_submitter.tables import Archive

T = TypeVar('T')

DATABASE_FILE: IO[bytes]


def setUpModule() -> None:
    global DATABASE_FILE

    DATABASE_FILE = tempfile.NamedTemporaryFile(suffix='sqlite.db')
    url = 'sqlite:///{}'.format(DATABASE_FILE.name)

    environ['TESTING'] = 'True'
    environ['DATABASE_URL'] = url

    create_engine(url)

    alembic.command.upgrade(Config('alembic.ini'), 'head')


class AppTests(unittest.TestCase):
    def await_(self, awaitable: Awaitable[T]) -> T:
        return self.loop.run_until_complete(awaitable)

    def setUp(self) -> None:
        super().setUp()

        # App import must happen after TESTING environment setup
        from code_submitter.server import app, database

        test_client = TestClient(app)
        self.session = test_client.__enter__()
        self.database = database
        self.loop = asyncio.get_event_loop()

    def tearDown(self) -> None:
        self.session.__exit__(None, None, None)
        super().tearDown()

    def test_app(self) -> None:
        response = self.session.get('/')
        self.assertEqual(200, response.status_code)

    def test_upload_file(self) -> None:
        contents = io.BytesIO()
        with zipfile.ZipFile(contents, mode='w') as zip_file:
            zip_file.writestr('robot.py', 'print("I am a robot")')

        response = self.session.post(
            '/upload',
            files={'archive': ('whatever.zip', contents.getvalue(), 'application/zip')},
        )
        self.assertEqual(200, response.status_code)

        archives = self.await_(
            self.database.fetch_all(Archive.select()),
        )

        self.assertEqual(
            [contents.getvalue()],
            [x['content'] for x in archives],
            "Wrong content stored in the database",
        )

    def test_upload_bad_file(self) -> None:
        response = self.session.post(
            '/upload',
            files={'archive': ('whatever.zip', b'should-be-a-zip', 'application/zip')},
        )
        self.assertEqual(400, response.status_code)

        count = self.await_(
            self.database.fetch_val(Archive.count()),
        )

        self.assertEqual(
            0,
            count,
            "Should not have stored anything in the databsae",
        )
