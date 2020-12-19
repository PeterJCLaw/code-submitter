from pathlib import Path

import test_utils
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.applications import Starlette
from starlette.authentication import AuthenticationError

from code_submitter.auth import (
    FileBackend,
    NemesisBackend,
    BLUESHIRT_SCOPE,
    NemesisUserInfo,
)


class NemesisAuthTests(test_utils.AsyncTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.info = NemesisUserInfo({
            'username': 'user',
            'first_name': 'Dave',
            'last_name': 'McDave',
            'teams': ['team-ABC'],
            'is_blueshirt': False,
            'is_student': True,
            'is_team_leader': False,
        })
        self.fake_nemesis = Starlette()
        self.backend = NemesisBackend(self.fake_nemesis, url='http://nowhere/')

    def test_not_authenticated(self) -> None:
        @self.fake_nemesis.route('/user/user')
        async def endpoint(request: Request) -> Response:
            return JSONResponse(
                {'authentication_errors': [
                    'NO_USERNAME',
                    'NO_PASSWORD',
                    'WRONG_PASSWORD',
                ]},
                status_code=403,
            )

        with self.assertRaises(AuthenticationError):
            self.await_(self.backend.validate('user', 'pass'))

    def test_ok(self) -> None:
        @self.fake_nemesis.route('/user/user')
        async def endpoint(request: Request) -> Response:
            return JSONResponse(self.info)

        scopes, user = self.await_(self.backend.validate('user', 'pass'))

        self.assertEqual(['authenticated'], scopes, "Wrong scopes for user")

        self.assertEqual('user', user.username, "Wrong username for user")
        self.assertEqual('ABC', user.team, "Wrong team for user")

    def test_no_team(self) -> None:
        @self.fake_nemesis.route('/user/user')
        async def endpoint(request: Request) -> Response:
            self.info['teams'] = []
            return JSONResponse(self.info)

        scopes, user = self.await_(self.backend.validate('user', 'pass'))

        self.assertIsNone(user.team, "Wrong team for user")
        self.assertEqual('user', user.username, "Wrong username for user")

        self.assertEqual(['authenticated'], scopes, "Wrong scopes for user")

    def test_multiple_teams(self) -> None:
        @self.fake_nemesis.route('/user/user')
        async def endpoint(request: Request) -> Response:
            self.info['teams'] = ['team-DEF', 'team-ABC']
            return JSONResponse(self.info)

        scopes, user = self.await_(self.backend.validate('user', 'pass'))

        self.assertEqual('DEF', user.team, "Wrong team for user")
        self.assertEqual('user', user.username, "Wrong username for user")

        self.assertEqual(['authenticated'], scopes, "Wrong scopes for user")

    def test_blueshirt(self) -> None:
        @self.fake_nemesis.route('/user/user')
        async def endpoint(request: Request) -> Response:
            self.info['teams'] = []
            self.info['is_blueshirt'] = True
            return JSONResponse(self.info)

        scopes, user = self.await_(self.backend.validate('user', 'pass'))

        self.assertIsNone(user.team, "Wrong team for user")
        self.assertEqual('user', user.username, "Wrong username for user")

        self.assertEqual(
            ['authenticated', BLUESHIRT_SCOPE],
            scopes,
            "Wrong scopes for user",
        )


class FileAuthTests(test_utils.AsyncTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.backend = FileBackend(
            path=Path(__file__).parent / 'fixtures' / 'auth-file.yml',
        )

    def test_ok(self) -> None:
        scopes, user = self.await_(self.backend.validate('ABC', 'password1'))
        self.assertEqual(['authenticated'], scopes, "Wrong scopes for user")

        self.assertEqual('Team ABC', user.username, "Wrong username for user")
        self.assertEqual('ABC', user.team, "Wrong team for user")

    def test_unknown_user(self) -> None:
        with self.assertRaises(AuthenticationError) as e:
            self.await_(self.backend.validate('DEF', 'password1'))

        self.assertEqual(e.exception.args[0], FileBackend.UNKNOWN_USER_MESSAGE)

    def test_incorrect_password(self) -> None:
        with self.assertRaises(AuthenticationError) as e:
            self.await_(self.backend.validate('ABC', 'password2'))

        self.assertEqual(e.exception.args[0], FileBackend.UNKNOWN_USER_MESSAGE)

    def test_blueshirt(self) -> None:
        scopes, user = self.await_(self.backend.validate('SRX', 'bees'))

        self.assertIsNone(user.team, "Wrong team for user")
        self.assertEqual('Blueshirt', user.username, "Wrong username for user")

        self.assertEqual(
            ['authenticated', BLUESHIRT_SCOPE],
            scopes,
            "Wrong scopes for user",
        )
