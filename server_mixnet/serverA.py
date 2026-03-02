from config import Rounds
import socket
import time
import threading
import signal
import sys
import asyncio

import time
from config import ROUND_LEN, ROUND_NUM
from encryption import decrypt_private_key
from keys import serverA_private_key
from shuffle import shuffle, unshuffle

## RECEIVE FROM CLIENT

def setup():
    # Initialize dead drop with None values for each bucket
    global NUM_BUCKETS 
    NUM_BUCKETS = 100
    dead_drop = [None, None] * NUM_BUCKETS

def get_bucket_index(dead_drop_id):
    # Returns index of bucket for this message
    return int(dead_drop_id, 32) % NUM_BUCKETS

def get_new_message():
    # Returns index of message for this round, encrypted content
    # Listens on socket for new messages from client
    # leave this alone for now
# dead_drop_index(hash)(bytes) || encrypted message

# Receives messages from the client and stores them in a list
def receive_messages_from_client(ROUND_LEN):

    start_time = time.time()                            # Start timer for batch round
    messages_list = []                                  # Initialize empty list to store messages

    while time.time() - start_time < ROUND_LEN:          # Loop to receive messages until batch round ends
        new_message = get_new_message()                 # Function to receive a new message from the client
        messages_list.append(dead_drop[new_message])

# Decrypts first layer of encryption using server A's private key
def serverA_decrypt(messages_list):
    for messages in messages_list:
        messages_list1 = decrypt_private_key(serverA_private_key, messages)

# Shuffles the messages in messages_list using permutation
def serverA_shuffle(messages_list):
    serverA_shuffled_messages, i = shuffle(messages_list)
    serverA_permutations_dictionary[ROUND_NUM] = i          #Store permutation inside permutations dictionary with round number

## SEND TO CLIENT
# Unshuffles the messages in messages_list using inverse permutation
def serverA_unshuffle(serverB_unshuffled_messages):
    serverA_unshuffled_messages = unshuffle(serverB_unshuffled_messages, serverA_permutations_dictionary)


serverA_permutations_dictionary = {}
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
