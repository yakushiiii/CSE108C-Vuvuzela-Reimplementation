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
import config
from keys import serverA_public_key, serverB_public_key, serverC_public_key

server_A = "127.0.0.1"
port = 9000
server_A_pubK = "e4420b424085b51bad775e8384cc15c6ebc22c49cf169cd8635f56caa28283"

round_number = 1 #for now hardcoding the round_number

#creating client class to establish public and private keys
class Client:
    def __init__(self):
        #long term keypair for use
        self.private_key = x25519.X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        config.GLOBAL_CLIENT_COUNT += 1
        self.username = "client" + str(config.GLOBAL_CLIENT_COUNT) #for now hardcoding the username by the client number 
        #sending public key to directory.json file PUT THIS IN SERVER CODE

    #registers user by sending the information the server needs to add them to the the directory json
    def register_user(self, username, public_key):
        
        #have to serialize the public key to send over bytes
        pk_bytes = self.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        with open("directory.json", "r") as file:
            data = json.load(file)

        data["users"][self.username] = {"public_key": self.public_key}

        with open("directory.json", "w") as file:
            json.dump(data, file, indent=4)

    
    #ask entry server (serverA) for the json file to retrieve the user they want to communicate with:
    def retrieve_user_pubK(client_name):
        return

    #-------------------------------------------
    # Encryption
    #-------------------------------------------

    #creating a shared secret
    def shared_secret(self, client_2_public_key):
        shared_key = self.private_key.exchange(client_2_public_key)
        return shared_key
    
    #diffie hellman key exchange
    def diffie_hellman(self, client_2_public_key):
        info = b"first-layer-encryption"
        shared_key = self.private_key.exchange(client_2_public_key)

        encryption_key = HKDF(
            algorithm = hashes.SHA256(),
            length = config.GLOBAL_KEY_LEN,
            salt = config.GLOBAL_SALT,
            info = info,
        ).derive(shared_key)
        return encryption_key
    
    #encrypt actual message 
    def encrypt_message(self, encryption_key, message, round_number): #add round num later
        #for further security we pad all messages to be the same length
        required_message_len = 100
        if len(message) > required_message_len:
            raise ValueError("WARNING: The message is too long.")
        padded_message = message + b"\00" * (100 - len(required_message_len))

        #have to create a nonce, in the paper they use the round number
        #for now lets use a fixed value
        nonce = round_number.to_bytes(12, "big")
        aesgcm = AESGCM(encryption_key)
        ciphertext = aesgcm.encrypt(nonce, padded_message)
        return ciphertext
    
    def decrypt_message(self, encryption_key, ciphertext): #add round num later
        aesgcm = AESGCM(encryption_key)
        nonce = round_number.to_bytes(12, "big") #hardcode the nonce for now
        plaintext = aesgcm.decrypt(nonce, ciphertext)
        return plaintext
    
    def get_dead_drop_id(shared_secret, round_number):
        round_bytes = round_number.to_bytes(8, "big")
        dead_drop_id = hashlib.sha256(shared_secret + round_bytes).digest()
        return dead_drop_id[:16] #Vuvuzela uses 128-bit dead drop IDs
    
    #encrypting a layer, can call this three times for each server
    def layer_encryption(self, server_public_key, payload):
        server_epk = x25519.X25519PrivateKey.generate()
        info = b'onion-layer-encryption'
        sh_key = server_epk.exchange(server_public_key)
        key = HKDF(
            algorithm = hashes.SHA256(),
            length = config.GLOBAL_KEY_LEN,
            salt = config.GLOBAL_SALT,
            info = info,
        ).derive(sh_key)

        aesgcm = AESGCM(key)
        nonce = round_number.to_bytes(12, "big")
        ciphertext = aesgcm.encrypt(nonce, payload, None)

        epk_bytes = server_epk.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
        return epk_bytes + nonce + ciphertext

    def onion_encrypt(self, ciphertext, dead_drop_id, serverA_public_key=serverA_public_key, serverB_public_key=serverB_public_key, serverC_public_key=serverC_public_key): 
        #encrypting entry server first to swap server last
        layer3 = self.layer_encryption(serverA_public_key, dead_drop_id + ciphertext)
        layer2 = self.layer_encryption(serverB_public_key, layer3)
        layer1 = self.layer_encryption(serverC_public_key, layer2)
        return layer1

#def initiate_conection(client_2):

if __name__ == "__main__":
    client_1 = Client()
    client_2 = Client()

    shared1 = client_1.shared_secret(client_2.public_key)
    shared2 = client_2.shared_secret(client_1.public_key)
    assert shared1 == shared2

    df_client_1 = client_1.diffie_hellman(client_2.public_key)
    df_client_2 = client_2.diffie_hellman(client_1.public_key)
    assert df_client_1 == df_client_2

    print("Welcome to our anonymouse private metadata messaging service!")
    print("Please ensure you leave this program running in the background in order to maintain privacy.")

    while (1): #this while loop is for initiating the conversationg between two clients
        connect_client = input("Enter the username of client you want to communicate with: ")
        #change this to ask server1 the directory.json file
        if (connect_client == "" | connect_client == '\n' ):
            print("Not a valid user.")
            connect_client = input("Enter the username of client you want to communicate with: ")

        #find a way to ask the server for the public key of the client using the username. For now just hardcoding it
        shared1 = client_1.shared_secret(client_2.public_key)
        df_client_1 = client_1.diffie_hellman(client_2.public_key)

        print("You are now communicating with", connect_client)
        print('Enter "\\quit" to end the conversation')
        while(1): #this while loop is for sending messages between two clients, we can break out of this loop to end the conversation

            # creating the message to send
            message = input('> ')

            if message == "\\quit":
                break

            #if no message then fill message with "NO MESSAGE" to prevent leaking information about message length
            if message == "":
                message = "NO MESSAGE" 
                
            #create socket and connect to server
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((server_A, port))

            #encrypting message and establishing dead drop id
            ciphertext = client_1.encrypt_message(df_client_1, message, round_number)
            dead_drop_id = client_1.get_dead_drop_id(shared1, round_number)

            #onion encrypt the message
            onion_msg = client_1.onion_encrypt(ciphertext, dead_drop_id)

            #need to send the message in bytes so using struct to do this
            length = len(onion_msg)
            length_bytes = struct.pack("!I", length) 

            #sending the onion encrypted message to the server
            sock.sendall(length_bytes + onion_msg)

            #receiving data
            response = sock.recv(4096)
    
        
            sock.close()

