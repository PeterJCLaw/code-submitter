import unittest

from code_submitter import app
from starlette.testclient import TestClient


class AppTests(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        test_client = TestClient(app)
        self.session = test_client.__enter__()

    def tearDown(self) -> None:
        self.session.__exit__(None, None, None)
        super().tearDown()

    def test_app(self) -> None:
        response = self.session.get('/')
        self.assertEqual(200, response.status_code)

    def test_upload_file(self) -> None:
        response = self.session.post(
            '/upload',
            files={'archive': ('whatever.zip', b'should-be-a-zip', 'application/zip')},
        )
        self.assertEqual(200, response.status_code)
