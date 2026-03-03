from config import Rounds
import socket
import time
import threading
import signal
import sys
import asyncio
import hashlib

import time
from config import ROUND_LEN, ROUND_NUM
from encryption import decrypt_private_key
from keys import serverA_private_key
from shuffle import shuffle, unshuffle

## RECEIVE FROM CLIENT

def setup():
    # Initialize dead drop with None values for each bucket
    global new_messages_list
    new_messages_list = [None, None] * 100

# Receives messages from the client and stores them in a list
def receive_messages_from_client(ROUND_LEN):

    start_time = time.time()                            # Start timer for batch round

    while time.time() - start_time < ROUND_LEN:          # Loop to receive messages until batch round ends
        # Listen on socket for new messages from client
        #store socket at indexes to to know which clients to send it back to
        message = socket.recv(4096)                            # Receive message from client (blocking call)
        new_messages_list.append(message)

# Decrypts first layer of encryption using server A's private key
def serverA_decrypt(new_messages_list):
    for messages in new_messages_list:
        decrypted_message_listA = decrypt_private_key(serverA_private_key, messages)
    return decrypted_message_listA

# Shuffles the messages in messages_list using permutation
def serverA_shuffle(decrypted_messages_listA):
    serverA_shuffled_messages, i = shuffle(decrypted_messages_listA)
    serverA_permutations = i          #Store permutation inside permutations dictionary with round number
    return serverA_shuffled_messages, serverA_permutations

## SEND TO CLIENT
# Unshuffles the messages in messages_list using inverse permutation
def serverA_unshuffle(serverB_unshuffled_messages):
    serverA_unshuffled_messages = unshuffle(serverB_unshuffled_messages, serverA_permutations)
    return serverA_unshuffled_messages

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
def main():
    global serverA_permutations
    serverA_permutations = []
    try: 
        setup()
        receive_messages_from_client(ROUND_LEN)
        decrypted_message_listA = serverA_decrypt(new_messages_list)
        shuffled_messages_listA, serverA_permutations = serverA_shuffle(decrypted_message_listA)
    except:
        print("Error in server A")

"""
async def serverA(rounds):
    while True:
        r = await rounds.wait_next_round()
        print("Server A processing round", r)

        # collect client messages
        # shuffle
        # forward

"""