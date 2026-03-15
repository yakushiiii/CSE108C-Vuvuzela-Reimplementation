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

#just saving these locally because they are long term keys
serverA_pubK = "be4420b424085b51bad775e8384cc15c6ebc22c49cf169cd8635f56caa28283e"
serverB_pubK = "cee95351c9c12d143aa18aaf0e665b3f24aa7056d092c7f75131736ac0de6944"
serverC_pubK = "c3347a3b97843e798bf56dee5fa4485bc7453476ca47789f9b954b5496daaa1e"

#creating client class to establish user and all relevant functionality, initalized with socket as a parameter so that i could immediately start sending messages to the server 
class Client:
    def __init__(self, sock):
        #long term keypair for use
        self.private_key = x25519.X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.username = None
        self.partner = None
        self.partner_pubK = None
        self.round_lock = threading.Lock()
        self.signal = threading.Event()
        self.quit = False
        self.incoming_messages = queue.Queue()
        self.outgoing_input = queue.Queue()
        self.shared_secret = None
        self.dead_drop_id = None
        self.round_number = None
        #will not be considered an actual client until client registers
        self.register_user(self.public_key, sock)
        print("Your username is {self.username}")
        #to start server threading and peristent listening for server signals
        threading.Thread(target=self.listen, args=(sock,)).start()

    #registers user by sending the information the server needs to add them to the the directory json
    def register_user(self, public_key, sock):
        #have to serialize the public key to send over bytes
        pk_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        #sends json object (signal) to request a username
        #sends json object to server to be added to director so they can start sending messages
        username_req = {"type": "USERNAME_REQUEST", "public_key": pk_bytes}
        req_bytes = username_req.encode()
        sock.sendall(req_bytes)
        data = sock.recv_all(sock)
        parsed_user_signal = json.loads(data)
        if (parsed_user_signal["type"] == "USERNAME"):
            self.username = parsed_user_signal["username"]
 
        
    #for getting messages, save a queue and the once start_send self.phase = "start_send" then everyone send message
    #if queue receives signal and is empty send a dummy message

    #get the username of the person the client is communicating with
    def get_partner(self):
        self.partner = input("Enter the username of client you want to communicate with: ")
        while (self.partner == "" or self.partner == '\n' ):
                print("Not a valid user.")
                self.partner = input("Enter the username of client you want to communicate with: ")
        return self.partner

    def listen(self, sock):
        while 1: 
            data = sock.recv_all(sock)
            parsed_json = json.loads(data)
            #parse json data and get round number
            if (parsed_json["type"] == "START_SEND"):
                self.phase = "START_SEND"
                self.round = parsed_json["round_number"]
                if self.phases == "START_SEND":
                    self.send_message(sock)
                #this signal tells queue to send message
                self.signal.set()
                #with self.round_lock:
                #    self.round = parsed_json["round_num"]
            elif (parsed_json["type"] == "START_RECIEVE"):
                self.phase = "START_RECIEVE"
                #continue so it listens for more input
                continue
            elif (parsed_json["type"] == "DIRECTORY" and self.partner != None):
                data - sock.recv_all(sock)
                directory = json.loads(data)
                public_key_hex = directory["users"][self.partner]["public_key"]
                public_key_bytes = bytes.fromhex(public_key_hex)
                self.partner_pubK = x25519.X25519PublicKey.from_public_bytes(public_key_bytes)
                continue
            elif (self.partner == None):
                #need just send dummy messages if there is no partner
                self.dummy_message()
            elif(self.partner != None and self.phase == "START_RECIEVE"):
                encrypted_message = parsed_json[self.partner]

    def send_message(self, sock):
        #shouldn't be anything in queue
        if self.outgoing_input.empty():
            sock.sendall(self.dummy_message())
        else: 
            message = self.outgoing_input.get()
            if message == "\\quit":
                self.quit = True
                sock.sendall(self.dummy_message())
            #add encryption
            else:
                ciphertext = encryption.encrypt_message(self.shared_secret, self.outgoing_input.get(), self.round)
                onion_packet = encryption.onion_encrypt(self.round, ciphertext, self.dead_drop_id, serverA_pubK, serverB_pubK, serverC_pubK)
                sock.sendall(onion_packet)

    def dummy_message(self):
        #dummy message is just going to be a bunch of random bytes. If the cleint can't decrypt the message using the shared key then that is how we know it is a dummy message to nothing will be displayed
        dummy = os.random(116)
        return dummy
        #onion encrypt this
        
    
    def input_loop(self):
        while True:
            msg = input("> ")
            self.outgoing_input.put(msg)



    
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

    print("Welcome to our anonymouse private metadata messaging service!")
    print("Please ensure you leave this program running in the background in order to maintain privacy. If you terminate this program your username will alse be reassigned.")
    print("Also note there is about a 10-20 second latency for message sending/recieving.")

    client = Client(sock)

    #shared1 = encryption.shared_secret(client.private_key, client.partner_pubK)
    #shared2 = encryption.shared_secret(client.private_key, client.public_key)
    #assert shared1 == shared2

    #df_client_2 = encryption.diffie_hellman(client_2.private_key, client_1.public_key)
    #assert df_client_1 == df_client_2

    #last = server_A.rounds.round_num


    while (1): #this while loop is for initiating the conversationg between two clients
        client.get_partner()
        client.shared_secret = encryption.shared_secret(client.private_key, client.partner_pubK)
        true_shared_secret = client.private_key.exchange(client.partner_pubK)
        # i manually key exchange becaues the shared_secret function produces a HKDF derives key based on the true shared secret, but we need the raw shared secret for the dead drop id
        client.dead_drop_id = encryption.get_dead_drop_id(true_shared_secret, client.round_number)
        client.quit = False

        #change this to ask server1 the directory.json file
      
        print("You are now communicating with", client.partner)
        print('Enter "\\quit" to end the conversation')
        while(1): #this while loop is for sending messages between two clients, we can break out of this loop to end the conversation
            if client.quit == True:
                break
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

            #await rounds.start_wait(round)

            #await server_A.start_recv(round)

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
"""
-------------------
Vuvuzela Encryption
-------------------

2 types of encryption:
    1. Message encryption (between users, used to encrypt the actual chat message)
    2. Onion encrpytion (between client and server, used to hide which dead drop the message goes to)

Step 1:
    Users generate a shared secret using Diffie Hellman(client_1_private, client_2_public) to produce a shared symmetrc key
Step 2:
    Compute the Dead Drop ID computed by hashing the shared secret + round number (so this changes every round)
Step 3:
    Encrypt the message using the shared secret computed earlier using Diffie Hellman.
Step 4: 
    Onion encrypt the message + dead_drop_id for every server, one layer on top of the other. For each server the client creates an ephemeral key pair and sends the encrypted message with the public key, so the server can compute a shared secret and then decrypt.
"""

"""""
def try_decrypt(key, nonce, ciphertext):
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext
    except Exception:
        return None

result = try_decrypt(key, nonce, ciphertext)"
"""
