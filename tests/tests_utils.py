from __future__ import annotations

import io
import zipfile
import datetime

import test_utils

from code_submitter import utils
from code_submitter.tables import Archive, ChoiceHistory


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

    def test_get_chosen_submissions_info_nothing_chosen(self) -> None:
        result = self.await_(utils.get_chosen_submissions_info(self.database))
        self.assertEqual([], result)

    def test_get_chosen_submissions_info_multiple_chosen(self) -> None:
        self.await_(self.database.execute(
            ChoiceHistory.insert().values(
                archive_id=8888888888,
                username='someone_else',
                created=datetime.datetime(2020, 8, 8, 12, 0),
            ),
        ))
        self.await_(self.database.execute(
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

        result = self.await_(utils.get_chosen_submissions_info(self.database))
        self.assertCountEqual(
            [
                utils.SubmissionInfo(
                    team='SRZ2',
                    archive_id=1111111111,
                    chosen_at=datetime.datetime(2020, 3, 3, 12, 0),
                ),
                utils.SubmissionInfo(
                    team='ABC',
                    archive_id=8888888888,
                    chosen_at=datetime.datetime(2020, 8, 8, 12, 0),
                ),
            ],
            result,
        )

    def test_get_chosen_submissions_nothing_chosen(self) -> None:
        result = self.await_(utils.get_chosen_submissions(self.database))
        self.assertEqual({}, result)

    def test_get_chosen_submissions_multiple_chosen(self) -> None:
        self.await_(self.database.execute(
            ChoiceHistory.insert().values(
                archive_id=8888888888,
                username='someone_else',
                created=datetime.datetime(2020, 8, 8, 12, 0),
            ),
        ))
        self.await_(self.database.execute(
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

        result = self.await_(utils.get_chosen_submissions(self.database))
        self.assertEqual(
            {
                'SRZ2': (1111111111, b'1111111111'),
                'ABC': (8888888888, b'8888888888'),
            },
            result,
        )

    def test_collect_submissions(self) -> None:
        self.await_(self.database.execute(
            ChoiceHistory.insert().values(
                archive_id=8888888888,
                username='someone_else',
                created=datetime.datetime(2020, 8, 8, 12, 0),
            ),
        ))
        self.await_(self.database.execute(
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

        with zipfile.ZipFile(io.BytesIO(), mode='w') as zf:
            self.await_(utils.collect_submissions(self.database, zf))

            self.assertEqual(
                {
                    'summary.txt': b'ABC: 8888888888\nSRZ2: 1111111111\n',
                    'SRZ2.zip': b'1111111111',
                    'ABC.zip': b'8888888888',
                },
                {x: zf.open(x).read() for x in zf.namelist()},
            )
