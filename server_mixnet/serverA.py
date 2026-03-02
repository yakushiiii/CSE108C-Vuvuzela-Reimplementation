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
    global NUM_BUCKETS 
    NUM_BUCKETS = 100
    global dead_drop
    dead_drop = [None, None] * NUM_BUCKETS

def get_bucket_index(dead_drop_hash):
    # Returns index of bucket for this message
    hash_to_int = int.from_bytes(dead_drop_hash, byteorder='big')
    bucket_id = hash_to_int % NUM_BUCKETS
    return bucket_id

# Receives messages from the client and stores them in a list
def receive_messages_from_client(ROUND_LEN):

    start_time = time.time()                            # Start timer for batch round

    while time.time() - start_time < ROUND_LEN:          # Loop to receive messages until batch round ends
        # Listen on socket for new messages from client
        #message = socket.recv(4096)                            # Receive message from client (blocking call)
        dead_drop_hash = message[0:32]                      # first 32 bytes of message is the hash of the dead drop index
        encrypted_message = message[32:]                    # rest of the message is the encrypted content     
        bucket_id = get_bucket_index(dead_drop_hash)          # Get bucket index for the new message
        dead_drop.insert(bucket_id, encrypted_message)

# Decrypts first layer of encryption using server A's private key
def serverA_decrypt(dead_drop):
    for messages in dead_drop:
        decrypted_message_listA = decrypt_private_key(serverA_private_key, messages)
    return decrypted_message_listA

# Shuffles the messages in messages_list using permutation
def serverA_shuffle(decrypted_messages_listA):
    serverA_shuffled_messages, i = shuffle(decrypted_messages_listA)
    serverA_permutations_dictionary[ROUND_NUM] = i          #Store permutation inside permutations dictionary with round number
    return serverA_shuffled_messages, serverA_permutations_dictionary

## SEND TO CLIENT
# Unshuffles the messages in messages_list using inverse permutation
def serverA_unshuffle(serverB_unshuffled_messages):
    serverA_unshuffled_messages = unshuffle(serverB_unshuffled_messages, serverA_permutations_dictionary)


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
    global serverA_permutations_dictionary 
    serverA_permutations_dictionary = {}
    try: 
        setup()
        receive_messages_from_client(ROUND_LEN)
        decrypted_message_listA = serverA_decrypt(dead_drop)
        shuffled_messages_listA, serverA_permutations_dictionary = serverA_shuffle(decrypted_message_listA)
    except:
        print("Error in server A")
