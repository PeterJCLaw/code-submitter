import base64
import binascii
from typing import Tuple, Optional, Sequence

from starlette.requests import HTTPConnection
from starlette.responses import Response
from starlette.authentication import (
    SimpleUser,
    AuthCredentials,
    AuthenticationError,
    AuthenticationBackend,
)


class User(SimpleUser):
    def __init__(self, username: str, team: str) -> None:
        super().__init__(username)
        self.team = team


ValidationResult = Tuple[Sequence[str], User]


def auth_required_response(conn: HTTPConnection, exc: Exception) -> Response:
    return Response(
        headers={'WWW-Authenticate': 'Basic realm=Code Submitter'},
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
    async def validate(self, username: str, password: str) -> ValidationResult:
        if not username:
            raise AuthenticationError("Must provide a username")
        if not password:
            raise AuthenticationError("Must provide a password")
        return ['authenticated'], User(username, 'SRZ')
