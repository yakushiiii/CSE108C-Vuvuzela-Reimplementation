import threading
import time
import asyncio
import os

ROUND_LEN = 3.0
SERVER_PORT = 9000
connections = 0
ROUND_NUM = 0
MAX_ROUND = 100000
duration = 20

#encryption global variables
GLOBAL_SALT = b"vuvuzela protocol v1"
GLOBAL_KEY_LEN = 32

#defining a class for incrementing rounds and resetting when round number gets too high
class Rounds:
    def __init__(self):
        self.round_num = 0
        self.max_round = 100000
    def increment(self):
        self.round_num += 1
        if self.round_num > self.max_round:
            self.round_num = 0
            