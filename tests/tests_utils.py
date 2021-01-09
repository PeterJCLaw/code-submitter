import io
import zipfile
import datetime

import test_utils

from code_submitter import utils
from code_submitter.tables import (
    Archive,
    Session,
    ChoiceHistory,
    ChoiceForSession,
)


class UtilsTests(test_utils.InTransactionTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.await_(self.database.execute(
            Archive.insert().values(
                id=8888888888,
                content=b'8888888888',
                username='someone_else',
                team='ABC',
                created=datetime.datetime(2020, 8, 8, 12, 0),
            ),
        ))
        self.await_(self.database.execute(
            Archive.insert().values(
                id=2222222222,
                content=b'2222222222',
                username='a_colleague',
                team='SRZ2',
                created=datetime.datetime(2020, 2, 2, 12, 0),
            ),
        ))
        self.await_(self.database.execute(
            Archive.insert().values(
                id=1111111111,
                content=b'1111111111',
                username='test_user',
                team='SRZ2',
                created=datetime.datetime(2020, 1, 1, 12, 0),
            ),
        ))

    def test_get_chosen_submissions_nothing_chosen(self) -> None:
        result = self.await_(
            utils.get_chosen_submissions(self.database, session_id=0),
        )
        self.assertEqual({}, result)

    def test_get_chosen_submissions_multiple_chosen(self) -> None:
        choice_id_1 = self.await_(self.database.execute(
            ChoiceHistory.insert().values(
                archive_id=8888888888,
                username='someone_else',
                created=datetime.datetime(2020, 8, 8, 12, 0),
            ),
        ))
        choice_id_2 = self.await_(self.database.execute(
            ChoiceHistory.insert().values(
                archive_id=1111111111,
                username='test_user',
                created=datetime.datetime(2020, 3, 3, 12, 0),
            ),
        ))
        self.await_(self.database.execute(
            ChoiceHistory.insert().values(
                archive_id=2222222222,
                username='test_user',
                created=datetime.datetime(2020, 2, 2, 12, 0),
            ),
        ))
        session_id = self.await_(self.database.execute(
            Session.insert().values(
                name="Test session",
                username='blueshirt',
            ),
        ))
        self.await_(self.database.execute(
            ChoiceForSession.insert().values(
                choice_id=choice_id_1,
                session_id=session_id,
            ),
        ))
        self.await_(self.database.execute(
            ChoiceForSession.insert().values(
                choice_id=choice_id_2,
                session_id=session_id,
            ),
        ))

        result = self.await_(
            utils.get_chosen_submissions(self.database, session_id),
        )
        self.assertEqual(
            {
                'SRZ2': (1111111111, b'1111111111'),
                'ABC': (8888888888, b'8888888888'),
            },
            result,
        )

    def test_create_session(self) -> None:
        choice_id_1 = self.await_(self.database.execute(
            ChoiceHistory.insert().values(
                archive_id=8888888888,
                username='someone_else',
                created=datetime.datetime(2020, 8, 8, 12, 0),
            ),
        ))
        choice_id_2 = self.await_(self.database.execute(
            ChoiceHistory.insert().values(
                archive_id=1111111111,
                username='test_user',
                created=datetime.datetime(2020, 3, 3, 12, 0),
            ),
        ))
        self.await_(self.database.execute(
            ChoiceHistory.insert().values(
                archive_id=2222222222,
                username='test_user',
                created=datetime.datetime(2020, 2, 2, 12, 0),
            ),
        ))

        session_id = self.await_(utils.create_session(
            self.database,
            "Test Session",
            by_username='the-user',
        ))

        choices = self.await_(self.database.fetch_all(
            ChoiceForSession.select(),
        ))

        self.assertEqual(
            [
                {'choice_id': choice_id_1, 'session_id': session_id},
                {'choice_id': choice_id_2, 'session_id': session_id},
            ],
            [dict(x) for x in choices],
        )

    def test_collect_submissions(self) -> None:
        choice_id_1 = self.await_(self.database.execute(
            ChoiceHistory.insert().values(
                archive_id=8888888888,
                username='someone_else',
                created=datetime.datetime(2020, 8, 8, 12, 0),
            ),
        ))
        choice_id_2 = self.await_(self.database.execute(
            ChoiceHistory.insert().values(
                archive_id=1111111111,
                username='test_user',
                created=datetime.datetime(2020, 3, 3, 12, 0),
            ),
        ))
        self.await_(self.database.execute(
            ChoiceHistory.insert().values(
                archive_id=2222222222,
                username='test_user',
                created=datetime.datetime(2020, 2, 2, 12, 0),
            ),
        ))
        session_id = self.await_(self.database.execute(
            Session.insert().values(
                name="Test session",
                username='blueshirt',
            ),
        ))
        self.await_(self.database.execute(
            ChoiceForSession.insert().values(
                choice_id=choice_id_1,
                session_id=session_id,
            ),
        ))
        self.await_(self.database.execute(
            ChoiceForSession.insert().values(
                choice_id=choice_id_2,
                session_id=session_id,
            ),
        ))

        with zipfile.ZipFile(io.BytesIO(), mode='w') as zf:
            self.await_(utils.collect_submissions(self.database, zf, session_id))

            self.assertEqual(
                {
                    'summary.txt': b'ABC: 8888888888\nSRZ2: 1111111111\n',
                    'SRZ2.zip': b'1111111111',
                    'ABC.zip': b'8888888888',
                },
                {x: zf.open(x).read() for x in zf.namelist()},
            )
