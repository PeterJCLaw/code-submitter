import base64
import logging
import binascii
from typing import cast, List, Tuple, Optional, Sequence
from typing_extensions import TypedDict

import httpx
from starlette.requests import HTTPConnection
from starlette.responses import Response
from starlette.applications import Starlette
from starlette.authentication import (
    SimpleUser,
    AuthCredentials,
    AuthenticationError,
    AuthenticationBackend,
)

logger = logging.getLogger(__name__)


class User(SimpleUser):
    def __init__(self, username: str, team: Optional[str]) -> None:
        super().__init__(username)
        self.team = team


ValidationResult = Tuple[Sequence[str], User]


def auth_required_response(conn: HTTPConnection, exc: Exception) -> Response:
    return Response(
        "You must login to submit code.",
        headers={'WWW-Authenticate': 'Basic realm="Student Robotics\' Code Submitter"'},
        status_code=401,
    )


def extract_basic_auth(auth_header: str) -> Tuple[str, str]:
    try:
        scheme, credentials = auth_header.split()
        if scheme.lower() != 'basic':
            raise AuthenticationError("Invalid auth scheme")
        decoded = base64.b64decode(credentials).decode('ascii')
    except (ValueError, UnicodeDecodeError, binascii.Error):
        raise AuthenticationError("Invalid basic auth credentials")

    username, _, password = decoded.partition(':')
    return username, password


class BasicAuthBackend(AuthenticationBackend):
    async def validate(self, username: str, password: str) -> ValidationResult:
        raise NotImplementedError(
            "Implementations must provide a 'validate' method",
        )

    async def authenticate(
        self,
        request: HTTPConnection,
    ) -> Optional[Tuple[AuthCredentials, User]]:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            raise AuthenticationError("Bees")

        username, password = extract_basic_auth(auth_header)
        scopes, user = await self.validate(username, password)
        return AuthCredentials(scopes), user


class DummyBackend(BasicAuthBackend):
    def __init__(self, team: Optional[str] = 'SRZ') -> None:
        self.team = team

    async def validate(self, username: str, password: str) -> ValidationResult:
        if not username:
            raise AuthenticationError("Must provide a username")
        if not password:
            raise AuthenticationError("Must provide a password")
        return ['authenticated'], User(username, self.team)


NemesisUserInfo = TypedDict('NemesisUserInfo', {
    'username': str,
    'first_name': str,
    'last_name': str,
    'teams': List[str],
    'is_blueshirt': bool,
    'is_student': bool,
    'is_team_leader': bool,
})


class NemesisBackend(BasicAuthBackend):
    def __init__(
        self,
        _target: Optional[Starlette] = None,
        *,
        url: str,
        verify: bool = True,
    ) -> None:
        # Munge types to cope with httpx not supporting strict_optional but
        # actually being fine with given `None`. Note we expect only to pass
        # this value in tests, so need to cope with it being `None` most of the
        # time anyway.
        app = cast(Starlette, _target)
        self.client = httpx.AsyncClient(base_url=url, app=app, verify=verify)

    async def load_user(self, username: str, password: str) -> NemesisUserInfo:
        async with self.client as client:
            respone = await client.get(
                'user/{}'.format(username),
                auth=(username, password),
            )

            try:
                respone.raise_for_status()
            except httpx.HTTPError as e:
                if e.response.status_code != 403:
                    logger.exception(
                        "Failed to contact nemesis while trying to authenticate %r",
                        username,
                    )
                raise AuthenticationError(e) from e

            return cast(NemesisUserInfo, respone.json())

    def strip_team(self, team: str) -> str:
        # All teams from nemesis *should* start with this prefix...
        if team.startswith('team-'):
            return team[len('team-'):]
        return team

    def get_team(self, info: NemesisUserInfo) -> Optional[str]:
        teams = [self.strip_team(x) for x in info['teams']]

        if not teams:
            if info['is_student']:
                logger.warning("Competitor %r has no teams!", info['username'])
            return None

        team = teams[0]

        if len(teams) > 1:
            logger.warning(
                "User %r is in more than one team (%r), using %r",
                info['username'],
                teams,
                team,
            )

        return team

    async def validate(self, username: str, password: str) -> ValidationResult:
        if not username:
            raise AuthenticationError("Must provide a username")
        if not password:
            raise AuthenticationError("Must provide a password")

        info = await self.load_user(username, password)

        team = self.get_team(info)

        return ['authenticated'], User(username, team)
