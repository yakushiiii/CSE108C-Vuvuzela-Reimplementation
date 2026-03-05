import threading
import time
import asyncio
import os
from enum import Enum

SERVER_PORT = 9000
connections = 0
MAX_ROUND = 100000
BATCHING = 20
NUM_BUCKETS = 100

#encryption global variables
GLOBAL_SALT = b"vuvuzela protocol v1"
GLOBAL_KEY_LEN = 32

#initializing phases to mark what part of round we are in
class Phase(Enum):
    SEND = 1
    WAIT = 2
    RECV = 3

#defining a class for incrementing rounds and resetting when round number gets too high
class Rounds:
    def __init__(self):
        self.round_num = 0
        self.max_round = 100000
        self.phase = Phase.SEND
        self.cv = asyncio.Condition()

    def increment(self):
        self.round_num += 1
        if self.round_num > self.max_round:
            self.round_num = 0

    #these three functions are for the server
    #signal client to start sending messages because the new round has started
    async def signal_new_round(self) -> int:
        async with self.cv:
            self.increment()
            self.phase =  Phase.SEND
            self.cv.notify_all()
            return self.round_num
        
    #signal for client to wait between sending and receiving messages
    async def signal_client_wait(self, round_num):
        async with self.cv:
            if self.round_num == round_num:
                self.phase = Phase.WAIT
                self.cv.notify_all()

    #signal for client to start receiving messages from serverA 
    async def signal_client_recv(self, round_num):
        async with self.cv:
            if self.round_num == round_num:
                self.phase = Phase.RECV
                self.cv.notify_all()

    #these three functions are for the client
    #next two functions are wait period between client stopping sending messages and client starting to receive them
    async def start_send(self, last_seen):
        async with self.cv:
            await self.cv.wait_for(lambda: self.phase == Phase.SEND and self.round_num != last_seen)
            return self.round_num
            
    async def start_recv(self, r):
        async with self.cv:
            await self.cv.wait_for(lambda: self.phase == Phase.RECV and self.round_num == r)
            
    async def start_wait(self, r):
        async with self.cv:
            await self.cv.wait_for(lambda: self.phase == Phase.WAIT and self.round_num == r)
 
    


#in serverA
"""
asycn def init_rounds():
    rounds = Rounds()
    asyncio.create_task(rounds.server_A())
    await asyncio.Event().wait()

async def server_A(rounds: Rounds):

    while True:
        round = await.rounds.signal_new_round()

        if (condition1):
            await.rounds.signal_client_wait(round)

        if (condition2):
            await.rounds.signal_client_recv(round)

--in main func---
asyncio.run(server_A())
"""

#in clients
"""""
last = rounds.round_num
while True:
    round = await rounds.startt_send(last)
    last = round


'"""

#make one for start and stop

#start -> stop sending messages

#on stop receiving a new rounds starts