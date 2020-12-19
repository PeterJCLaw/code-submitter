import io
import zipfile
import datetime
from unittest import mock

import test_utils
from starlette.testclient import TestClient

from code_submitter.auth import BLUESHIRT_SCOPE
from code_submitter.tables import Archive, ChoiceHistory


class AppTests(test_utils.DatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        # App import must happen after TESTING environment setup
        from code_submitter.server import app

        def url_for(name: str) -> str:
            # While it makes for uglier tests, we do need to use more absolute
            # paths here so that the urls emitted contain the root_path from the
            # ASGI server and in turn work correctly under proxy.
            return 'http://testserver{}'.format(app.url_path_for(name))

        test_client = TestClient(app)
        self.session = test_client.__enter__()
        self.session.auth = ('test_user', 'test_pass')
        self.url_for = url_for

    def tearDown(self) -> None:
        self.session.__exit__(None, None, None)
        super().tearDown()

    def test_app(self) -> None:
        response = self.session.get(self.url_for('homepage'))
        self.assertEqual(200, response.status_code)

        html = response.text
        self.assertIn("Upload a new submission", html)

    def test_app_requires_auth(self) -> None:
        self.session.auth = None
        response = self.session.get(self.url_for('homepage'))
        self.assertEqual(401, response.status_code)
        self.assertIn('WWW-Authenticate', response.headers)
        self.assertIn(' realm=', response.headers['WWW-Authenticate'])

    def test_shows_own_and_own_team_uploads(self) -> None:
        self.await_(self.database.execute(
            # Another team's archive we shouldn't be able to see.
            Archive.insert().values(
                id=8888888888,
                content=b'',
                username='someone_else',
                team='ABC',
                created=datetime.datetime(2020, 8, 8, 12, 0),
            ),
        ))
        self.await_(self.database.execute(
            Archive.insert().values(
                id=2222222222,
                content=b'',
                username='a_colleague',
                team='SRZ2',
                created=datetime.datetime(2020, 2, 2, 12, 0),
            ),
        ))
        self.await_(self.database.execute(
            Archive.insert().values(
                id=1111111111,
                content=b'',
                username='test_user',
                team='SRZ2',
                created=datetime.datetime(2020, 1, 1, 12, 0),
            ),
        ))

        response = self.session.get(self.url_for('homepage'))
        self.assertEqual(200, response.status_code)

        html = response.text
        self.assertIn('2020-01-01', html)
        self.assertIn('1111111111', html)
        self.assertIn('test_user', html)

        self.assertIn('2020-02-02', html)
        self.assertIn('2222222222', html)
        self.assertIn('a_colleague', html)

        self.assertNotIn('2020-08-08', html)
        self.assertNotIn('8888888888', html)
        self.assertNotIn('someone_else', html)

    def test_shows_chosen_archive(self) -> None:
        self.await_(self.database.execute(
            # Another team's archive we shouldn't be able to see.
            Archive.insert().values(
                id=8888888888,
                content=b'',
                username='someone_else',
                team='ABC',
                created=datetime.datetime(2020, 8, 8, 12, 0),
            ),
        ))
        self.await_(self.database.execute(
            Archive.insert().values(
                id=2222222222,
                content=b'',
                username='a_colleague',
                team='SRZ2',
                created=datetime.datetime(2020, 2, 2, 12, 0),
            ),
        ))
        self.await_(self.database.execute(
            Archive.insert().values(
                id=1111111111,
                content=b'',
                username='test_user',
                team='SRZ2',
                created=datetime.datetime(2020, 1, 1, 12, 0),
            ),
        ))
        self.await_(self.database.execute(
            # An invalid choice -- you shouldn't be able to select archives for
            # another team.
            ChoiceHistory.insert().values(
                archive_id=8888888888,
                username='test_user',
                created=datetime.datetime(2020, 9, 9, 12, 0),
            ),
        ))
        self.await_(self.database.execute(
            ChoiceHistory.insert().values(
                archive_id=2222222222,
                username='test_user',
                created=datetime.datetime(2020, 3, 3, 12, 0),
            ),
        ))

        response = self.session.get(self.url_for('homepage'))
        self.assertEqual(200, response.status_code)

        html = response.text
        self.assertIn('2020-01-01', html)
        self.assertIn('1111111111', html)
        self.assertIn('test_user', html)

        self.assertIn('2020-02-02', html)
        self.assertIn('2222222222', html)
        self.assertIn('a_colleague', html)

        self.assertIn('2020-03-03', html)

        self.assertNotIn('2020-08-08', html)
        self.assertNotIn('8888888888', html)
        self.assertNotIn('someone_else', html)

        self.assertNotIn('2020-09-09', html)

    def test_upload_file(self) -> None:
        contents = io.BytesIO()
        with zipfile.ZipFile(contents, mode='w') as zip_file:
            zip_file.writestr('robot.py', 'print("I am a robot")')

        response = self.session.post(
            self.url_for('upload'),
            files={'archive': ('whatever.zip', contents.getvalue(), 'application/zip')},
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(
            self.url_for('homepage'),
            response.headers['location'],
        )

        archives = self.await_(
            self.database.fetch_all(Archive.select()),
        )

        self.assertEqual(
            [contents.getvalue()],
            [x['content'] for x in archives],
            "Wrong content stored in the database",
        )

        self.assertEqual(
            ['test_user'],
            [x['username'] for x in archives],
            "Wrong username stored in the database",
        )

        self.assertEqual(
            ['SRZ2'],
            [x['team'] for x in archives],
            "Wrong team stored in the database",
        )

        choices = self.await_(
            self.database.fetch_all(ChoiceHistory.select()),
        )
        self.assertEqual([], choices, "Should not have created a choice")

    def test_upload_and_choose_file(self) -> None:
        contents = io.BytesIO()
        with zipfile.ZipFile(contents, mode='w') as zip_file:
            zip_file.writestr('robot.py', 'print("I am a robot")')

        response = self.session.post(
            self.url_for('upload'),
            data={'choose': 'on'},
            files={'archive': ('whatever.zip', contents.getvalue(), 'application/zip')},
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(
            self.url_for('homepage'),
            response.headers['location'],
        )

        archive, = self.await_(
            self.database.fetch_all(Archive.select()),
        )

        self.assertEqual(
            contents.getvalue(),
            archive['content'],
            "Wrong content stored in the database",
        )

        choices = self.await_(
            self.database.fetch_all(ChoiceHistory.select()),
        )
        self.assertEqual(
            [{
                'archive_id': archive['id'],
                'username': 'test_user',
                'id': mock.ANY,
                'created': mock.ANY,
            }],
            [dict(x) for x in choices],
            "Should not have created a choice",
        )

    def test_upload_bad_file(self) -> None:
        response = self.session.post(
            self.url_for('upload'),
            files={'archive': ('whatever.zip', b'should-be-a-zip', 'application/zip')},
        )
        self.assertEqual(400, response.status_code)

        archives = self.await_(
            self.database.fetch_all(Archive.select()),
        )
        self.assertEqual([], archives, "Wrong content stored in the database")

        choices = self.await_(
            self.database.fetch_all(ChoiceHistory.select()),
        )
        self.assertEqual([], choices, "Should not have created a choice")

    def test_upload_archive_without_robot_py(self) -> None:
        contents = io.BytesIO()
        with zipfile.ZipFile(contents, mode='w') as zip_file:
            zip_file.writestr('main.py', 'print("I am a robot")')

        response = self.session.post(
            self.url_for('upload'),
            files={'archive': ('whatever.zip', contents.getvalue(), 'application/zip')},
        )
        self.assertEqual(400, response.status_code)

        archives = self.await_(
            self.database.fetch_all(Archive.select()),
        )
        self.assertEqual([], archives, "Wrong content stored in the database")

        choices = self.await_(
            self.database.fetch_all(ChoiceHistory.select()),
        )
        self.assertEqual([], choices, "Should not have created a choice")

    def test_no_download_link_for_non_blueshirt(self) -> None:
        download_url = self.url_for('download_submissions')

        response = self.session.get(self.url_for('homepage'))

        html = response.text
        self.assertNotIn(download_url, html)

    def test_shows_download_link_for_blueshirt(self) -> None:
        self.session.auth = (BLUESHIRT_SCOPE, BLUESHIRT_SCOPE)

        download_url = self.url_for('download_submissions')

        response = self.session.get(self.url_for('homepage'))
        html = response.text
        self.assertIn(download_url, html)

    def test_download_submissions_requires_blueshirt(self) -> None:
        response = self.session.get(self.url_for('download_submissions'))
        self.assertEqual(403, response.status_code)

    def test_download_submissions_when_none(self) -> None:
        self.session.auth = (BLUESHIRT_SCOPE, BLUESHIRT_SCOPE)

        response = self.session.get(self.url_for('download_submissions'))
        self.assertEqual(200, response.status_code)

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            self.assertCountEqual(
                ['summary.txt'],
                zf.namelist(),
            )

    def test_download_submissions(self) -> None:
        self.session.auth = (BLUESHIRT_SCOPE, BLUESHIRT_SCOPE)

        self.await_(self.database.execute(
            Archive.insert().values(
                id=8888888888,
                content=b'',
                username='someone_else',
                team='ABC',
                created=datetime.datetime(2020, 8, 8, 12, 0),
            ),
        ))
        self.await_(self.database.execute(
            ChoiceHistory.insert().values(
                archive_id=8888888888,
                username='test_user',
                created=datetime.datetime(2020, 9, 9, 12, 0),
            ),
        ))

        response = self.session.get(self.url_for('download_submissions'))
        self.assertEqual(200, response.status_code)

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            self.assertCountEqual(
                ['summary.txt', 'ABC.zip'],
                zf.namelist(),
            )
