#!/usr/bin/env python3

import asyncio
import argparse
from pathlib import Path

import databases

from . import utils, config


async def async_main(submissions_directory: Path) -> None:
    submissions_directory.mkdir(parents=True, exist_ok=True)

    database = databases.Database(config.DATABASE_URL)

    async with database.transaction():
        submissions = await utils.get_chosen_submissions(database)

        for team, content in submissions.items():
            (submissions_directory / f'{team.upper()}.zip').write_bytes(content)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('submissions_directory', type=Path)
    return parser.parse_args()


def main(args: argparse.Namespace) -> None:
    asyncio.get_event_loop().run_until_complete(async_main(args.submissions_directory))


if __name__ == '__main__':
    main(parse_args())
