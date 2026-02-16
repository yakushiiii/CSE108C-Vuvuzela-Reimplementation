from config import Rounds
import socket
import time
import threading
import signal
import sys
import asyncio
import time
from config import duration

## RECEIVE FROM CLIENT

# Initialize 1000 empty mailboxes
mailboxes = [None] * 1000

# Receives messages from the client and stores them in a list
def receive_messages_from_client(message, duration):

    # Start timer for batch round
    start_time = time.time()

    # Initialize empty list to store messages
    messages_list = []

    # Loop to receive messages until batch round ends
    while time.time() - start_time < duration:
        messages_list = messages_list.append(message)

def handle_connection(conn: socket.socket, addr):
    try:
        data = conn.recv(4096)
        #do something with this data
    finally: 
        conn.close()


def serverA():
    pass


def main(): 
    if len(sys.argv) < 2:
        print(f"wrong argumets: {sys.argv[0]} port_num", file=sys.stderr)
        print(f"usage: {sys.argv[0]} <port>", file=sys.stderr)
        return 1
    
    try:
        port = int(sys.argv[1], 10)
    except ValueError:
        sys.stderr.write("Invalid Port\n")

if __name__ == "__main__":
    raise SystemExit(main())
