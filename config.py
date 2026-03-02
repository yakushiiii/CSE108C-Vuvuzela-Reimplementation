import threading
import time
import asyncio
import os

ROUND_LEN = 20
SERVER_PORT = 9000
connections = 0
MAX_ROUND = 100000

#encryption global variables
GLOBAL_SALT = b"vuvuzela protocol v1"
GLOBAL_KEY_LEN = 32

#defining a class for incrementing rounds and resetting when round number gets too high
class Rounds:
    def __init__(self):
        self.round_num = 0
        self.max_round = 100000
        self.round_len = ROUND_LEN

        self._event = asyncio.Event()
        self._next_tick = time.monotonic() + self.round_len

    def increment(self):
        self.round_num += 1
        if self.round_num > self.max_round:
            self.round_num = 0

    def signal_new_round(self):
        self.increment()
        self._event.set()
        self._event = asyncio.Event()

    async def wait_next_round(self) -> int:
        await self._event.wait()
        return self.round_num
    
    async def run(self):
        while True:
            now = time.monotonic()
            sleep_time = max(0.0, self._next_tick - now)
            await asyncio.sleep(sleep_time)
            self._next_tick += self.round_len

            self.signal_new_round()


            