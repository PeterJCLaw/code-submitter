import test_utils
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.applications import Starlette
from starlette.authentication import AuthenticationError

from code_submitter.auth import NemesisBackend, NemesisUserInfo


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
            ['authenticated', 'blueshirt'],
            scopes,
            "Wrong scopes for user",
        )
