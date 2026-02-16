#client file

import socket 
import asyncio 
import os
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


server_1 = "127.0.0.1"
port = 9000

shared_key = 12 #for now incremment this by one, then once client is working use actual encryption
client_id_1 = 1 #for now hardcoding client id
client_id_2 = 2 #for now harcoding other client id

#creating client class to establish public and private keys
class client:
    def __init__(self):
        self.private_key = x25519.X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()

#def onion_encrypt(client, message): 
        

if __name__ == "__main__":
    client_1 = client()
    print(client_1.private_key)
    print(client_1.public_key)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #sock.connect(server_1, port)

    #sock.send(onion_message)
    #response = sock.recv(4096)