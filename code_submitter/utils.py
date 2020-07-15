from typing import Dict, Tuple
from zipfile import ZipFile

import databases
from sqlalchemy.sql import select

from .tables import Archive, ChoiceHistory


async def get_chosen_submissions(
    database: databases.Database,
) -> Dict[str, Tuple[int, bytes]]:
    """
    Return a mapping of teams to their the chosen archive.
    """

    # Note: Ideally we'd group by team in SQL, however that doesn't seem to work
    # properly -- we don't get the ordering applied before the grouping.

    rows = await database.fetch_all(
        select([
            Archive.c.id,
            Archive.c.team,
            Archive.c.content,
            ChoiceHistory.c.created,
        ]).select_from(
            Archive.join(ChoiceHistory),
        ).order_by(
            Archive.c.team,
            ChoiceHistory.c.created.asc(),
        ),
    )

    # Rely on later keys replacing earlier occurrences of the same key.
    return {x['team']: (x['id'], x['content']) for x in rows}


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
