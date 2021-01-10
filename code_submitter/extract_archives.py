#!/usr/bin/env python3

import asyncio
import zipfile
import argparse
from typing import cast
from pathlib import Path

import databases
from sqlalchemy.sql import select

from . import utils, config
from .tables import Session


async def async_main(output_archive: Path, session_name: str) -> None:
    output_archive.parent.mkdir(parents=True, exist_ok=True)

    database = databases.Database(config.DATABASE_URL)

    session_id = cast(int, await database.fetch_one(select([
        Session.c.id,
    ]).where(
        Session.c.name == session_name,
    )))

    with zipfile.ZipFile(output_archive) as zf:
        async with database.transaction():
            utils.collect_submissions(database, zf, session_id)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('session_name', type=str)
    parser.add_argument('output_archive', type=Path)
    return parser.parse_args()


def main(args: argparse.Namespace) -> None:
    asyncio.get_event_loop().run_until_complete(
        async_main(args.output_archive, args.session_name),
    )


if __name__ == '__main__':
    main(parse_args())
