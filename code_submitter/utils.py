import datetime
from typing import (
    Any,
    Dict,
    Tuple,
    Union,
    TypeVar,
    Callable,
    Iterable,
    Collection,
)
from zipfile import ZipFile
from typing_extensions import TypedDict

import databases
from sqlalchemy.sql import select, FromClause, ColumnElement

from .tables import Archive, ChoiceHistory

K = TypeVar('K')
V = TypeVar('V')
R = TypeVar('R')

# Replicate a type from sqlalchemy, telling mypy to ignore the Any.
SqlalchemyField = Union['ColumnElement[Any]', FromClause, int]  # type:ignore[misc]


def map_values(mapping: Dict[K, V], fn: Callable[[V], R]) -> Dict[K, R]:
    return {k: fn(v) for k, v in mapping.items()}


async def _get_chosen_submissions_data(
    database: databases.Database,
    fields: Iterable[SqlalchemyField],
) -> Dict[str, databases.interfaces.Record]:
    """
    Return a mapping of teams to their the chosen archive.
    """

    # Note: Ideally we'd group by team in SQL, however that doesn't seem to work
    # properly -- we don't get the ordering applied before the grouping.

    rows = await database.fetch_all(
        select([
            *fields,
            Archive.c.team.label('__team'),
        ]).select_from(
            Archive.join(ChoiceHistory),
        ).order_by(
            Archive.c.team,
            ChoiceHistory.c.created.asc(),
        ),
    )

    # Rely on later keys replacing earlier occurrences of the same key.
    return {x['__team']: x for x in rows}


class SubmissionInfo(TypedDict):
    team: str
    archive_id: int
    chosen_at: datetime.datetime


async def get_chosen_submissions_info(
    database: databases.Database,
) -> Collection[SubmissionInfo]:
    """
    Return a mapping of teams to their the chosen archive.
    """

    submissions_by_team = await _get_chosen_submissions_data(database, [
        Archive.c.id,
        ChoiceHistory.c.created,
    ])
    return [
        SubmissionInfo(
            team=team,
            archive_id=info['id'],
            chosen_at=info['created'],
        )
        for team, info in submissions_by_team.items()
    ]


async def get_chosen_submissions(
    database: databases.Database,
) -> Dict[str, Tuple[int, bytes]]:
    """
    Return a mapping of teams to their the chosen archive.
    """
    submissions_by_team = await _get_chosen_submissions_data(database, [
        Archive.c.id,
        Archive.c.content,
    ])
    return {
        team: (row['id'], row['content'])
        for team, row in submissions_by_team.items()
    }


def summarise(submissions: Dict[str, Tuple[int, bytes]]) -> str:
    return "".join(
        "{}: {}\n".format(team, id_)
        for team, (id_, _) in sorted(submissions.items())
    )


async def collect_submissions(
    database: databases.Database,
    zipfile: ZipFile,
) -> None:
    submissions = await get_chosen_submissions(database)

    for team, (_, content) in submissions.items():
        zipfile.writestr(f'{team.upper()}.zip', content)

    zipfile.writestr('summary.txt', summarise(submissions))
