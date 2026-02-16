from config import Rounds
import socket
import time
import threading
import signal
import sys
import asyncio

import time
from config import duration, ROUND_NUM
from encryption import decrypt_private_key
from keys import serverA_private_key
from shuffle import shuffle, unshuffle

## RECEIVE FROM CLIENT

def get_new_message():
    # Returns index of message for this round, encrypted content
    # Listens on socket for new messages from client
    pass

# Receives messages from the client and stores them in a list
def receive_messages_from_client(duration):
    start_time = time.time()                            # Start timer for batch round
    messages_list = []                                  # Initialize empty list to store messages

    while time.time() - start_time < duration:          # Loop to receive messages until batch round ends
        new_message = get_new_message()                 # Function to receive a new message from the client
        messages_list.append(new_message)

# Decrypts first layer of encryption using server A's private key
def serverA_decrypt(messages_list):
    for messages in messages_list:
        messages_list1 = decrypt_private_key(serverA_private_key, messages)

# Shuffles the messages in messages_list using permutation
def serverA_shuffle(messages_list):
    serverA_shuffled_messages, i = shuffle(messages_list)
    serverA_permutations_dictionary[ROUND_NUM] = i   

## SEND TO CLIENT
# Unshuffles the messages in messages_list using inverse permutation
def serverA_unshuffle(serverB_unshuffled_messages):
    serverA_unshuffled_messages = unshuffle(serverB_unshuffled_messages)


serverA_permutations_dictionary = {}
################################################################################
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
        sys.stderr.write("Invalid Port\n")

if __name__ == "__main__":
    raise SystemExit(main())
