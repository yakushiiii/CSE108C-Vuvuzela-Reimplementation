from config import Rounds
import socket
import time
import threading
import signal
import sys
import asyncio

import time
from config import duration
from cryptography.hazamat.primitives.asymmetric import rsa, padding
from cryptography.hazamat.primitives import serialization, hashes
from cryptography.hazamat.primitives import default_backend

## RECEIVE FROM CLIENT

def get_new_message():
    # Returns index of message for this round, encrypted content
    # Listens on socket for new messages from client
    pass

# Receives messages from the client and stores them in a list
def receive_messages_from_client(duration):

    # Start timer for batch round
    start_time = time.time()

    # Initialize empty list to store messages
    messages_list = []

    # Loop to receive messages until batch round ends
    while time.time() - start_time < duration:
        new_message = get_new_message() # Function to receive a new message from the client
        messages_list.append(new_message)

def serverA_shuffle(messages_list):
    # Decrypts first layer of encryption using server A's private key
    
    # Shuffles the messages in messages_list using permutation

    # Stores permutation and sender's temporary public key for server A

    pass
    





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
