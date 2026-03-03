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
        self.cv_sendm = asyncio.Condition()
        self.cv_recvm = asyncio.Condition()
    


    def increment(self):
        self.round_num += 1
        if self.round_num > self.max_round:
            self.round_num = 0
    
    #signal client to start sending messages because the new round has started
    async def signal_new_round(self) -> int:
        async with self.cv_recvm:
            self.increment()
            self.cv_sendm.notify_all()
            await self.cv_recvm.wait_for(lambda: self.signal_client_recv)
            return self.round_num

    async def signal_client_recv(self):
        async with self.cv_recvm:
            self.cv_recvm.notify_all()

    #signal for client to stop sending messages and for 
    async def stop_messaging(self):
        async with self.cv_sendm and self.cv_recvm:
            await self.cv_sendm.wait_for(lambda: self.signal_new_round())
            self.cv_sendm.notify_all()

    #wait period between client stopping sending messages and client starting to receive them
    async def wait_period(self):
        async with self.cv_recvm:
            await self.cv_sendm.wait_for(lambda: self.signal_new_round())
            
 
    


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