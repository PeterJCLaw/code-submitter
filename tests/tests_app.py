import io
import zipfile
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
