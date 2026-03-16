#client file

import socket 
import os
import struct
import json
import secrets
import string
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from helper_functions import encryption
import threading
import queue
import time
import config

#encryption global variables
GLOBAL_SALT = b"vuvuzela protocol v1"
GLOBAL_KEY_LEN = 32
GLOBAL_MESSAGE_LEN = 256
GLOBAL_ENCRYPTED_LEN = 468

server_A = "192.168.64.7"

#just saving these locally because they are long term keys
serverA_pubK = x25519.X25519PublicKey.from_public_bytes(bytes.fromhex(
    "be4420b424085b51bad775e8384cc15c6ebc22c49cf169cd8635f56caa28283e"
))
serverB_pubK = x25519.X25519PublicKey.from_public_bytes(bytes.fromhex(
    "cee95351c9c12d143aa18aaf0e665b3f24aa7056d092c7f75131736ac0de6944"
))
serverC_pubK = x25519.X25519PublicKey.from_public_bytes(bytes.fromhex(
    "c3347a3b97843e798bf56dee5fa4485bc7453476ca47789f9b954b5496daaa1e"
))

#creating client class to establish user and all relevant functionality, initalized with socket as a parameter so that i could immediately start sending messages to the server 
class Client:
    def __init__(self, sock):
        #long term keypair for use
        self.private_key = x25519.X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.username = None
        self.partner = None
        self.partner_pubK = None
        self.signal = threading.Event()
        self.quit = False
        self.outgoing_input = queue.Queue()
        self.shared_secret = None
        self.dead_drop_id = None
        self.round_number = None
        self.server_client_sh_keys = []
        self.sock_lock = threading.Lock()
        self.phase = "WAIT"
        #will not be considered an actual client until client registers
        self.register_user(self.public_key, sock)
        print(f"Your username is {self.username}")
        #to start server threading and peristent listening for server signals
        

    #registers user by sending the information the server needs to add them to the the directory json
    def register_user(self, public_key, sock):
        #have to serialize the public key to send over bytes
        pk_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        #sends json object (signal) to request a username
        #sends json object to server to be added to director so they can start sending messages
        username_req = {"type": "USERNAME_REQUEST", "public_key": pk_bytes.hex()}
        req_bytes = json.dumps(username_req).encode()
        print("CLIENT: sending USERNAME_REQUEST")
        with self.sock_lock:
            send_packet(sock, req_bytes)
            print("CLIENT: waiting for username response")
            data = recv_all(sock)
        print("CLIENT: got username response:", data)
        parsed_user_signal = json.loads(data)
        while (parsed_user_signal["type"] != "USERNAME"):
            with self.sock_lock:
                send_packet(sock, req_bytes)
                print("CLIENT: waiting for username response")
                data = recv_all(sock)
                parsed_user_signal = json.loads(data)
            continue
        self.username = parsed_user_signal["username"]
 
        
    #for getting messages, save a queue and the once start_send self.phase = "start_send" then everyone send message
    #if queue receives signal and is empty send a dummy message

    #get the username of the person the client is communicating with
    def get_partner(self, sock):
        self.partner = input("Enter the username of client you want to communicate with: ")
        while (self.partner == "" or self.partner == '\n' ):
                print("Not a valid user.")
                self.partner = input("Enter the username of client you want to communicate with: ")
        with self.sock_lock:
            partner_pubK_req = {"type": "PARTNER_PUBLIC_KEY_REQUEST"}
            req_bytes = json.dumps(partner_pubK_req).encode()
            send_packet(sock, req_bytes)
            data = recv_all(sock)
        directory = json.loads(data)
        while self.partner not in directory["users"]:
            print("User does not exist. Please try again.")
            self.partner = input("Enter the username of client you want to communicate with: ")
            while (self.partner == "" or self.partner == '\n' ):
                print("Not a valid user.")
                self.partner = input("Enter the username of client you want to communicate with: ")

        public_key_hex = directory["users"][self.partner]["public_key"]
        public_key_bytes = bytes.fromhex(public_key_hex)
        self.partner_pubK = x25519.X25519PublicKey.from_public_bytes(public_key_bytes)
        self.shared_secret = encryption.shared_secret(self.private_key, self.partner_pubK)
        return self.partner

    def listen(self, sock):
        count = 0
        while 1: 
            with self.sock_lock:
                data = recv_all(sock)
            parsed_json = json.loads(data)
            #parse json data and get round number
            if ((parsed_json["type"] != "START_SEND") and count == 0):
                continue
            else:
                count += 1
            if (parsed_json["type"] == "START_SEND"):
                self.phase = "START_SEND"
                self.round_number = parsed_json["round_number"]
                self.send_message(sock)
            elif (parsed_json["type"] == "START_RECEIVE"):
                self.phase = "START_RECEIVE"
                #here is where the client gets the packet and decrypts it 
                if(self.partner != None and self.phase == "START_RECEIVE"):
                    cipher_len = struct.unpack("!I", recv_msg(sock, 4))[0]
                    ciphertext = recv_msg(sock,cipher_len)
                    plaintext_message = encryption.onion_decrypt(self.server_client_sh_keys, ciphertext, self.shared_secret, self.round_number)
                    if plaintext_message is not None:
                        print(f"{self.partner} > {plaintext_message.rstrip(b'\x00').decode(errors='ignore')}")
                else:
                    #pretend to receive a message just dont print anything
                    cipher_len = struct.unpack("!I", recv_msg(sock, 4))[0]
                    ciphertext = recv_msg(sock,cipher_len)
                
    #need just send dummy messages if there is no partner
    def send_message(self, sock):
        #shouldn't be anything in queue
        if self.partner != None:
            raw_shared = self.private_key.exchange(self.partner_pubK)
            self.dead_drop_id = encryption.get_dead_drop_id(raw_shared, self.round_number)
            if self.outgoing_input.empty():
                onion_packet, self.server_client_sh_keys = encryption.onion_encrypt(self.round_number, self.shared_secret, self.dummy_message(), self.dead_drop_id, serverA_pubK, serverB_pubK, serverC_pubK)
                send_packet(sock, onion_packet)
            else: 
                message = self.outgoing_input.get()
                if message == "\\quit":
                    self.quit = True
                    onion_packet, self.server_client_sh_keys = encryption.onion_encrypt(self.round_number, self.shared_secret, self.dummy_message(), self.dead_drop_id, serverA_pubK, serverB_pubK, serverC_pubK)
                    send_packet(sock, onion_packet)
                    self.partner = None
                    self.partner_pubK = None
                    self.shared_secret = None
                    self.dead_drop_id = None
                #add encryption
                else:
                    onion_packet, self.server_client_sh_keys = encryption.onion_encrypt(self.round_number, self.shared_secret, message, self.dead_drop_id, serverA_pubK, serverB_pubK, serverC_pubK)
                    send_packet(sock, onion_packet)
        else:
            if self.outgoing_input.empty():
                fake_dead_drop = os.urandom(16)
                fake_shared_secret = os.urandom(32)
                onion_packet, self.server_client_sh_keys = encryption.onion_encrypt(self.round_number, fake_shared_secret, self.dummy_message(), fake_dead_drop, serverA_pubK, serverB_pubK, serverC_pubK)
                send_packet(sock, onion_packet)
            else:
                message = self.outgoing_input.get()
                if message == "\\new partner":
                    self.quit = False
                    fake_dead_drop = os.urandom(16)
                    fake_shared_secret = os.urandom(32)
                    onion_packet, self.server_client_sh_keys = encryption.onion_encrypt(self.round_number, fake_shared_secret, self.dummy_message(), fake_dead_drop, serverA_pubK, serverB_pubK, serverC_pubK)
                    send_packet(sock, onion_packet)
                    self.get_partner(sock)
                else:
                    fake_dead_drop = os.urandom(16)
                    fake_shared_secret = os.urandom(32)
                    onion_packet, self.server_client_sh_keys = encryption.onion_encrypt(self.round_number, fake_shared_secret, self.dummy_message(), fake_dead_drop, serverA_pubK, serverB_pubK, serverC_pubK)
                    send_packet(sock, onion_packet)


    def dummy_message(self):
        #dummy message is just going to be a bunch of random bytes. If the cleint can't decrypt the message using the shared key then that is how we know it is a dummy message to nothing will be displayed
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for i in range(116))
        #onion encrypt this
        
    
    def input_loop(self):
        while True:
            msg = input("> ")
            self.outgoing_input.put(msg)

#def initiate_conection(client_2):

def recv_msg(sock, message_length):
    response = b""
    while len(response) < message_length:
        chunk = sock.recv(message_length - len(response))
        if not chunk:
            raise ConnectionError("WARNING: Socket closed unexpectedly.")
        response += chunk
    return response

#for receiving signals or entire message
def send_packet(sock, payload: bytes):
    sock.sendall(struct.pack("!I", len(payload)) + payload)

def recv_all(sock):
    msg_len = struct.unpack("!I", recv_msg(sock, 4))[0]
    return recv_msg(sock, msg_len)
            
if __name__ == "__main__":
    #create socket and connect to server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_A, config.SERVER_PORT))

    print("Welcome to our anonymouse private metadata messaging service!")
    print("Please ensure you leave this program running in the background in order to maintain privacy. If you terminate this program your username will alse be reassigned.")
    print("Also note there is about a 10-20 second latency for message sending/recieving.")

    client = Client(sock)
    client.get_partner(sock)
    threading.Thread(target=client.listen, args=(sock,), daemon=True).start()
    threading.Thread(target=client.input_loop, daemon=True).start()


    while True:
        time.sleep(1)

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
