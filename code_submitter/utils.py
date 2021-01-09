from typing import cast, Dict, Tuple
from zipfile import ZipFile

import databases
from sqlalchemy.sql import select

from .tables import Archive, Session, ChoiceHistory, ChoiceForSession


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


async def create_session(
    database: databases.Database,
    name: str,
    *,
    by_username: str,
) -> int:
    """
    Return a mapping of teams to their the chosen archive.
    """

    # Note: Ideally we'd group by team in SQL, however that doesn't seem to work
    # properly -- we don't get the ordering applied before the grouping.

    async with database.transaction():
        rows = await database.fetch_all(
            select([
                ChoiceHistory.c.id,
                Archive.c.team,
            ]).select_from(
                Archive.join(ChoiceHistory),
            ).order_by(
                Archive.c.team,
                ChoiceHistory.c.created.asc(),
            ),
        )

        session_id = cast(int, await database.execute(
            Session.insert().values(name=name, username=by_username),
        ))

        # Rely on later keys replacing earlier occurrences of the same key.
        choice_by_team = {x['team']: x['id'] for x in rows}
        await database.execute_many(
            ChoiceForSession.insert(),
            [
                {'choice_id': x, 'session_id': session_id}
                for x in choice_by_team.values()
            ],
        )

    return session_id


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
