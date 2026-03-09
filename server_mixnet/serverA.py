from config import Rounds
import socket as sock
import time
import threading
import signal
import sys
import asyncio
import hashlib

import time
from config import NUM_BUCKETS, BATCHING

# Receives messages from the client and stores them in a list
def receive_messages_from_client(BATCHING):

    start_time = time.time()                            # Start timer for batch round

    while time.time() - start_time < BATCHING:          # Loop to receive messages until batch round ends
        # Listen on socket for new messages from client
        # store socket at indexes to to know which clients to send it back to
        response = sock.recv(4096)                          # Receive message from client (blocking call)
    
    return response

async def init_rounds():
    rounds = Rounds()
    asyncio.create_task(server_A(rounds))
    await asyncio.Event().wait()

async def server_A(rounds: Rounds):
    wait = 0
    receive = 0
    message_list = []
    round = await rounds.signal_new_round()
    #receiving data
    response = receive_messages_from_client()

    #have clients wait
    await rounds.signal_client_wait(round)
    print("Server A having clients wait...")

    #parse response and separate messages in a list
    for i in range(0, len(response), 468):
        message_list.append(response[i:i+468])

    print("Server A parsed messages")

    return message_list


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