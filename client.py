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
MAX_ROUNDS = 20

server_A = "169.233.123.148" #CHANGE

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
        self.sock_lock = threading.Lock()
        self.phase = "WAIT"
        self.partner_lookup_in_progress = False
        self.sock = sock
        self.round_state = {}
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
                print("CLIENT: waiting for username response")
                data = recv_all(sock)
                parsed_user_signal = json.loads(data)
            continue
        self.username = parsed_user_signal["username"]
 
        
    #for getting messages, save a queue and the once start_send self.phase = "start_send" then everyone send message
    #if queue receives signal and is empty send a dummy message

    #get the username of the person the client is communicating with
    def get_partner(self):
        self.partner_lookup_in_progress = True
        try:
            self.partner = input("Enter the username of client you want to communicate with: ")
            while self.partner == "" or self.partner == "\n":
                print("Not a valid user.")
                self.partner = input("Enter the username of client you want to communicate with: ")

            with open("directory.json", "r") as f:
                parsed_json = json.load(f)

            if "users" not in parsed_json:
                print("directory.json is missing 'users'")
                self.partner = None
                return None

            while self.partner not in parsed_json["users"]:
                print("User does not exist. Please try again.")
                self.partner = input("Enter the username of client you want to communicate with: ")
                while self.partner == "" or self.partner == "\n":
                    print("Not a valid user.")
                    self.partner = input("Enter the username of client you want to communicate with: ")

            public_key_hex = parsed_json["users"][self.partner]["public_key"]
            public_key_bytes = bytes.fromhex(public_key_hex)
            self.partner_pubK = x25519.X25519PublicKey.from_public_bytes(public_key_bytes)
            self.shared_secret = encryption.shared_secret(self.private_key, self.partner_pubK)
            self.partner_lookup_in_progress = False
            print(f"Now communicating with {self.partner}")
            print(f"Caution: please allow at least a minute to receive all partner messages before you quit, if not they will be lost.")
            return self.partner

        finally:
            self.partner_lookup_in_progress = False
        """"
        with self.sock_lock:
            partner_pubK_req = {"type": "PARTNER_PUBLIC_KEY_REQUEST"}
            req_bytes = json.dumps(partner_pubK_req).encode()
            send_packet(sock, req_bytes)
        """

    def listen(self, sock):
        count = 0
        while 1: 
            with self.sock_lock:
                data = recv_all(sock)
            try:
                parsed_json = json.loads(data)
            except:
                continue
            """"
            if isinstance(parsed_json, dict) and "users" in parsed_json:
                if self.partner not in parsed_json["users"]:
                    print("User does not exist. Please try again.")
                    self.partner_lookup_in_progress = False
                    self.partner = None
                    continue

                public_key_hex = parsed_json["users"][self.partner]["public_key"]
                public_key_bytes = bytes.fromhex(public_key_hex)
                self.partner_pubK = x25519.X25519PublicKey.from_public_bytes(public_key_bytes)
                self.shared_secret = encryption.shared_secret(self.private_key, self.partner_pubK)
                self.partner_lookup_in_progress = False
                print(f"Now communicating with {self.partner}")
                continue
            """
            #parse json data and get round number
            msg_type = parsed_json.get("type")
            if msg_type is None:
                continue
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
                with self.sock_lock:
                    ciphertext = recv_all(sock)
                #here is where the client gets the packet and decrypts it
                state = self.round_state.get(self.round_number) 
                if state is None:
                    continue
                server_keys = state["server_keys"]
                round_shared_secret = state["shared_secret"]
                round_partner = state["partner"]
                if(round_partner != None and round_shared_secret is not None):
                    #inner_len = struct.unpack("!I", ciphertext[:4])[0]
                    #ciphertext = ciphertext[4:4 + inner_len]
                    try:
                        plaintext_message = encryption.onion_decrypt(server_keys, ciphertext, round_shared_secret, self.round_number)
                        plaintext_message = plaintext_message.rstrip(b"\x00").decode(errors="ignore")
                        if plaintext_message != None and plaintext_message.startswith("> "):
                            print(f"\n{round_partner} {plaintext_message}")
                            print("> ", end="", flush=True)
                        else:
                            print(f"\n {plaintext_message}")
                    except: 
                        self.round_state.pop(self.round_number, None)   
                        continue                    
                self.round_state.pop(self.round_number, None)
                    
    #need just send dummy messages if there is no partner
    def send_message(self, sock):
        #shouldn't be anything in queue
        if self.partner != None and self.partner_pubK != None and self.shared_secret != None:
            raw_shared = self.private_key.exchange(self.partner_pubK)
            self.dead_drop_id = encryption.get_dead_drop_id(raw_shared, self.round_number)
            if self.outgoing_input.empty():
                dummy_text = self.dummy_message()
                onion_packet, keys = encryption.onion_encrypt(self.round_number, self.shared_secret, dummy_text, self.dead_drop_id, serverA_pubK, serverB_pubK, serverC_pubK)
                round_partner = self.partner
                round_shared_secret = self.shared_secret
                print("Dummy Message Sent")
            else: 
                message = self.outgoing_input.get()
                if message == "\\quit":
                    self.quit = True
                    dummy_text = self.dummy_message()
                    onion_packet, keys = encryption.onion_encrypt(self.round_number, self.shared_secret, dummy_text, self.dead_drop_id, serverA_pubK, serverB_pubK, serverC_pubK)
                    round_partner = self.partner
                    round_shared_secret = self.shared_secret
                    self.partner = None
                    self.partner_pubK = None
                    self.shared_secret = None
                    self.dead_drop_id = None
                #add encryption
                else:
                    message = "> " + message
                    onion_packet, keys = encryption.onion_encrypt(self.round_number, self.shared_secret, message, self.dead_drop_id, serverA_pubK, serverB_pubK, serverC_pubK)
                    round_partner = self.partner
                    round_shared_secret = self.shared_secret
        else:
            fake_dead_drop = os.urandom(16)
            fake_shared_secret = os.urandom(32)
            dummy_text = self.dummy_message()
            onion_packet, keys = encryption.onion_encrypt(self.round_number, fake_shared_secret, dummy_text, fake_dead_drop, serverA_pubK, serverB_pubK, serverC_pubK)
            round_partner = None
            round_shared_secret = None

            if not self.outgoing_input.empty():
                _ = self.outgoing_input.get()

        #to solve problem of not being able to decrypt next couple of rounds after quit save the round state for the next couple of rounds
        self.round_state[self.round_number] = {
            "server_keys": keys,
            "shared_secret": round_shared_secret,
            "partner": round_partner,
        }
        if len(self.round_state) > MAX_ROUNDS:
            oldest_round = min(self.round_state.keys())
            del self.round_state[oldest_round]

        with self.sock_lock:
            send_packet(sock, onion_packet)

    def dummy_message(self):
        #dummy message is just going to be a bunch of random bytes. If the cleint can't decrypt the message using the shared key then that is how we know it is a dummy message to nothing will be displayed
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for i in range(116))
        #onion encrypt this
        
    
    def input_loop(self):
        while True:
            msg = input("> ")
            if msg == "\\new partner":
                self.get_partner()
            else:
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
    print("Type: '\\new partner' to start messaging someone")

    client = Client(sock)
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
