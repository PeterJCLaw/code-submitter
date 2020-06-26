import unittest

from code_submitter import app
from starlette.testclient import TestClient


class AppTests(unittest.TestCase):
    def test_app(self) -> None:
        client = TestClient(app)
        response = client.get('/')
        self.assertEqual(200, response.status_code)

    def test_upload_file(self) -> None:
        client = TestClient(app)
        response = client.post(
            '/upload',
            files={'archive': ('whatever.zip', b'should-be-a-zip', 'application/zip')},
        )
        self.assertEqual(200, response.status_code)
