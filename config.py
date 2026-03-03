import threading
import time
import asyncio
import os

SERVER_PORT = 9000
connections = 0
MAX_ROUND = 100000
BATCHING = 20
NUM_BUCKETS = 100

#encryption global variables
GLOBAL_SALT = b"vuvuzela protocol v1"
GLOBAL_KEY_LEN = 32

#defining a class for incrementing rounds and resetting when round number gets too high
class Rounds:
    def __init__(self):
        self.round_num = 0
        self.max_round = 100000
        self.cv = asyncio.Condition()
    


    def increment(self):
        self.round_num += 1
        if self.round_num > self.max_round:
            self.round_num = 0

    async def signal_new_round(self) -> int:
        async with self.cv:
            self.increment()
            self.cv.notify_all()
            return self.round_num


    async def wait_next_round(self, last_seen):
        async with self.cv:
            await self.cv.wait_for(lambda: self.round_num != last_seen)
            return self.round_num
    


#in serverA
"""
async def server_A(rounds: Rounds):
    round_number = rounds.round_num
    while True:
        if (condition):
            round_number = await rounds.signal_new_round()
        await asyncio.sleep(0)
"""

#in clients
"""""
last = rounds.round_num
while True:
    rn = await rounds.wait_next_round(last)
    last = rn
'"""

#make one for start and stop

#start -> stop sending messages
#wait 
#start -> stop receiving messages
#on stop receiving a new rounds starts