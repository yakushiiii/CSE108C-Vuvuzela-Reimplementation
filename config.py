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
    RECV = 2

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
    
    #signal client to start sending messages because the new round has started
    async def signal_new_round(self) -> int:
        async with self.cv:
            self.increment()
            self.phase =  Phase.SEND
            self.cv.notify_all()
            return self.round_num
        
    #signal for client to start receiving messages from serverA 
    async def signal_client_recv(self, round_num):
        async with self.cv:
            if self.round_num == round_num:
                self.phase = Phase.RECV
                self.cv.notify_all()


    #next two functions are wait period between client stopping sending messages and client starting to receive them
    async def start_send(self, last_seen):
        async with self.cv:
            await self.cv.wait_for(lambda: self.phase == Phase.SEND and self.round_num != last_seen)
            return self.round_num
            
    async def start_recv(self, r):
        async with self.cv:
            await self.cv.wait_for(lambda: self.phase == Phase.RECV and self.round_num == r)
            
 
    


#in serverA
"""
async def server_A(rounds: Rounds):
    round_number = rounds.round_num
    while True:
        if (condition1):
            rounds.stop_messaging()

        if (condition2):
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

#on stop receiving a new rounds starts