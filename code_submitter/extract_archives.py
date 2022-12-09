#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import zipfile
import argparse
from pathlib import Path

import databases

from . import utils, config


async def async_main(output_archive: Path) -> None:
    output_archive.parent.mkdir(parents=True, exist_ok=True)

    database = databases.Database(config.DATABASE_URL)

    with zipfile.ZipFile(output_archive) as zf:
        async with database.transaction():
            await utils.collect_submissions(database, zf)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('output_archive', type=Path)
    return parser.parse_args()


def main(args: argparse.Namespace) -> None:
    asyncio.get_event_loop().run_until_complete(async_main(args.output_archive))


if __name__ == '__main__':
    main(parse_args())
