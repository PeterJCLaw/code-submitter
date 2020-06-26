import unittest

from code_submitter import app
from starlette.testclient import TestClient


class AppTests(unittest.TestCase):
    def test_app(self) -> None:
        client = TestClient(app)
        response = client.get('/')
        self.assertEqual(200, response.status_code)
