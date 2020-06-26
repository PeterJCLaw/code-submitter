import io
import zipfile
import tempfile
import unittest
from typing import IO

import alembic  # type: ignore[import]
from sqlalchemy import create_engine
from alembic.config import Config  # type: ignore[import]
from starlette.config import environ
from starlette.testclient import TestClient

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
    def setUp(self) -> None:
        super().setUp()

        # App import must happen after TESTING environment setup
        from code_submitter import app

        test_client = TestClient(app)
        self.session = test_client.__enter__()

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

    def test_upload_bad_file(self) -> None:
        response = self.session.post(
            '/upload',
            files={'archive': ('whatever.zip', b'should-be-a-zip', 'application/zip')},
        )
        self.assertEqual(400, response.status_code)
