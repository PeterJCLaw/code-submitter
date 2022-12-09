from __future__ import annotations

import json
import asyncio
import tempfile
import unittest
from typing import IO, TypeVar, Awaitable

import alembic
import databases
from sqlalchemy import create_engine
from alembic.config import Config
from starlette.config import environ

from code_submitter.auth import NemesisUserInfo, DummyNemesisBackend

T = TypeVar('T')


DATABASE_FILE: IO[bytes]


def ensure_database_configured() -> None:
    global DATABASE_FILE

    try:
        DATABASE_FILE
        return
    except NameError:
        pass

    DATABASE_FILE = tempfile.NamedTemporaryFile(suffix='sqlite.db')
    url = 'sqlite:///{}'.format(DATABASE_FILE.name)

    environ['TESTING'] = 'True'
    environ['DATABASE_URL'] = url

    environ['AUTH_BACKEND'] = json.dumps({
        'backend': 'code_submitter.auth.DummyNemesisBackend',
        'kwargs': {'data': [
            NemesisUserInfo({
                'username': 'test_user',
                'first_name': 'Test',
                'last_name': 'User',
                'teams': ['team-SRZ2'],
                'is_blueshirt': False,
                'is_student': False,
                'is_team_leader': False,
            }),
            NemesisUserInfo({
                'username': 'no_teams_blueshirt',
                'first_name': 'No Teams',
                'last_name': 'Blueshirt',
                'teams': [],
                'is_blueshirt': True,
                'is_student': False,
                'is_team_leader': False,
            }),
            *DummyNemesisBackend.DEFAULT,
        ]},
    })

    create_engine(url)

    alembic.command.upgrade(Config('alembic.ini'), 'head')


class AsyncTestCase(unittest.TestCase):
    def await_(self, awaitable: Awaitable[T]) -> T:
        return self.loop.run_until_complete(awaitable)

    def setUp(self) -> None:
        super().setUp()

        self.loop = asyncio.get_event_loop()


class DatabaseTestCase(AsyncTestCase):
    database: databases.Database

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        ensure_database_configured()

        # Import must happen after TESTING environment setup
        from code_submitter.server import database

        cls.database = database


class InTransactionTestCase(DatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.await_(self.database.connect())

    def tearDown(self) -> None:
        self.await_(self.database.disconnect())
        super().tearDown()
