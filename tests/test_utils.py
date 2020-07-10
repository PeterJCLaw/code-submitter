import asyncio
import unittest
from typing import TypeVar, Awaitable

T = TypeVar('T')


class AsyncTestCase(unittest.TestCase):
    def await_(self, awaitable: Awaitable[T]) -> T:
        return self.loop.run_until_complete(awaitable)

    def setUp(self) -> None:
        super().setUp()

        self.loop = asyncio.get_event_loop()
