from config import Rounds
import socket
import time
import threading
import signal
import sys
import asyncio
import hashlib

import time
from config import NUM_BUCKETS, BATCHING

## RECEIVE FROM CLIENT

def setupA():
    # Initialize dead drop with None values for each bucket
    global new_messages_list
    new_messages_list = [None, None] * NUM_BUCKETS

# Receives messages from the client and stores them in a list
def receive_messages_from_client(BATCHING):

    start_time = time.time()                            # Start timer for batch round

    while time.time() - start_time < BATCHING:          # Loop to receive messages until batch round ends
        # Listen on socket for new messages from client
        # store socket at indexes to to know which clients to send it back to
        message = socket.recv(4096)                            # Receive message from client (blocking call)
        new_messages_list.append(message)
    
    return new_messages_list

################################################################################

'''
def handle_connection(conn: socket.socket, addr):
    try:
        data = conn.recv(4096)
        #do something with this data
    finally: 
        conn.close()

def main(): 
    if len(sys.argv) < 2:
        print(f"wrong argumets: {sys.argv[0]} port_num", file=sys.stderr)
        print(f"usage: {sys.argv[0]} <port>", file=sys.stderr)
        return 1
    
    try:
        port = int(sys.argv[1], 10)
    except ValueError:
        sys.stderr.write("Invalid Port\n\")

if __name__ == "__main__":
    raise SystemExit(main())
'''

"""
async def serverA(rounds):
    while True:
        r = await rounds.wait_next_round()
        print("Server A processing round", r)

        # collect client messages
        # shuffle
        # forward

"""