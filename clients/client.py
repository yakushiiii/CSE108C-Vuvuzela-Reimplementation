#client file

import socket 
import asyncio 
import os
import hashlib
import struct
import json
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from keys import serverA_public_key, serverB_public_key, serverC_public_key
import client_functions
from helper_functions import encryption
import threading
import queue
import time

SERVER_PORT = 9000
connections = 0
MAX_ROUND = 100000
BATCHING = 20
NUM_BUCKETS = 100

#encryption global variables
GLOBAL_SALT = b"vuvuzela protocol v1"
GLOBAL_KEY_LEN = 32
GLOBAL_MESSAGE_LEN = 100
GLOBAL_ENCRYPTED_LEN = 468

server_A = "127.0.0.1"
port = 9000
server_A_pubK = "e4420b424085b51bad775e8384cc15c6ebc22c49cf169cd8635f56caa28283"

#creating client class to establish user and all relevant functionality, initalized with socket as a parameter so that i could immediately start sending messages to the server 
class Client:
    def __init__(self, sock):
        #long term keypair for use
        self.private_key = x25519.X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.username = None
        self.partner = None
        self.round_lock = threading.Lock()
        self.signal = threading.Event()
        #will not be considered an actual client until client registers
        self.register_user(self.public_key)
        #to start server threading and peristent listening for server signals
        threading.Thread(target=self.listen, args=(sock,)).start()
        
    

    
    #registers user by sending the information the server needs to add them to the the directory json
    def register_user(self, public_key):
        #have to serialize the public key to send over bytes
        pk_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        #should ask server for username
        
    #for getting messages, save a queue and the once start_send self.phase = "start_send" then everyone send message
    #if queue receives signal and is empty send a dummy message

    #get the username of the person the client is communicating with
    def get_partner(self):
        self.partner = input("Enter the username of client you want to communicate with: ")
        return self.partner

    def listen(self, sock):
        while 1: 
            data = sock.recv_all(sock)
            parsed_json = json.loads(data)
            #parse json data and get round number
            if (parsed_json["type"] == "START_SEND"):
                self.phase = "START_SEND"
                #this signal tells queue to send message
                self.signal.set()
                with self.round_lock:
                    self.round = parsed_json["round_num"]
            elif (parsed_json["type"] == "START_RECIEVE"):
                self.phase = "START_RECIEVE"
                break
            elif (self.partner == None):
                #need just send dummy messages if there is no partner



    
    #ask entry server (serverA) for the json file to retrieve the user they want to communicate with and then parse it:
    def retrieve_user_pubK(client_name):
        return

#def initiate_conection(client_2):

def recv_msg(sock):
    response = b""
    while len(response) < GLOBAL_ENCRYPTED_LEN:
        chunk = sock.recv(GLOBAL_ENCRYPTED_LEN - len(response))
        if not chunk:
            raise ConnectionError("WARNING: Socket closed unexpectedly.")
        response += chunk
    return response

#for receiving signals or entire message
def recv_all(sock):
    response = b""
    while 1:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response += chunk
    return response

#creating a class for multithreading so that the client is always waiting to receive signals from server even when it is waiting for input
#on register we want to start this
class ClientState:
    def __init__(self):
        self.round_lock = threading.Lock()
        self.phase = "WAIT"
        self.round = 0
        


#where we do all the functionality so it operates on a round system
async def client_main(rounds):
    #create socket and connect to server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_A, port))

    client_1 = Client(sock)

    shared1 = encryption.shared_secret(client_1.private_key, client_2.public_key)
    shared2 = encryption.shared_secret(client_2.private_key, client_1.public_key)
    assert shared1 == shared2

    df_client_1 = encryption.diffie_hellman(client_1.private_key, client_2.public_key)
    df_client_2 = encryption.diffie_hellman(client_2.private_key, client_1.public_key)
    assert df_client_1 == df_client_2

    print("Welcome to our anonymouse private metadata messaging service!")
    print("Please ensure you leave this program running in the background in order to maintain privacy. If you terminate this program your username will aslo be reassigned.")
    #last = server_A.rounds.round_num


    r = threading.Thread(target=recieving)
    r.start()

    while(1):
        while (1): #this while loop is for initiating the conversationg between two clients
            connect_client = client_1.get_partner()
            #change this to ask server1 the directory.json file
            if (connect_client == "" or connect_client == '\n' ):
                print("Not a valid user.")
                connect_client = input("Enter the username of client you want to communicate with: ")

            #find a way to ask the server for the public key of the client using the username. For now just hardcoding it
            shared1 = helper_functions.encryption.shared_secret(client_1.private_key, client_2.public_key)
            df_client_1 = helper_functions.encryption.diffie_hellman(client_1.private_key, client_2.public_key)

            print("You are now communicating with", connect_client)
            print('Enter "\\quit" to end the conversation')
            while(1): #this while loop is for sending messages between two clients, we can break out of this loop to end the conversation
                
                last = round
                # creating the message to send
                message = input('> ')

                if message == "\\quit":
                    break

                #if no message then fill message with "NO MESSAGE" to prevent leaking information about message length
                if message == "":
                    message = "NO MESSAGEfD83hsfdl39rjws" 

                #encrypting message and establishing dead drop id
                ciphertext = helper_functions.encryption.encrypt_message(df_client_1, message, round_number)
                dead_drop_id = helper_functions.encryption.get_dead_drop_id(shared1, round_number)

                #onion encrypt the message
                onion_msg = helper_functions.encryption.onion_encrypt(round_number, ciphertext, dead_drop_id)

                #sending the onion encrypted message to the server
                sock.sendall(onion_msg)

                await rounds.start_wait(round)

                await server_A.start_recv(round)

                #receiving data
                response = sock.recv(4096)
                print(response + "\n")
            
                sock.close()


if __name__ == "__main__":
    asyncio.run(client_main(rounds))



"""
async def client(rounds):
    while True:
        r = await rounds.wait_next_round()
        print("Client sending in round", r)

        # compute dead drop using r
        # build onion
        # send to server
"""
""""
while True:
    round = await rounds.startt_send(last)
    last = round
"""


#if dead drop hash the one the client is expecting dispaly if not don't

#save shared keys


"""""
with open("directory.json", "r") as file:
            data = json.load(file)
        data["users"][username] = {"public_key": pk_bytes}
        with open("directory.json", "w") as file:
            json.dump(data, file, indent=4)
"""