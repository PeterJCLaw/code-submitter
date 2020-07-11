from typing import Dict

import databases
from sqlalchemy.sql import select

from .tables import Archive, ChoiceHistory


async def get_chosen_submissions(database: databases.Database) -> Dict[str, bytes]:
    """
    Return a mapping of teams to their the chosen archive.
    """

    # Note: Ideally we'd group by team in SQL, however that doesn't seem to work
    # properly -- we don't get the ordering applied before the grouping.

    rows = await database.fetch_all(
        select([
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
    return {x['team']: x['content'] for x in rows}
