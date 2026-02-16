#client file

import socket 
import asyncio 
import os
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import serialization
from config import GLOBAL_KEY_LEN, GLOBAL_SALT

server_1 = "127.0.0.1"
port = 9000

client_id_1 = 1 #for now hardcoding client id
client_id_2 = 2 #for now harcoding other client id

#creating client class to establish public and private keys
class Client:
    def __init__(self):
        self.private_key = x25519.X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
    
    #creating a shared secret
    def shared_secret(self, client_2_public_key):
        shared_key = self.private_key.exchange(client_2_public_key)
        return shared_key
    
    #diffie hellman key exchange
    def diffie_hellman(self, client_2_public_key):
        info = b"first layer encryption"
        shared_key = self.private_key.exchange(client_2_public_key)

        encryption_key = HKDF(
            algorithm = hashes.SHA256(),
            length = GLOBAL_KEY_LEN,
            salt = GLOBAL_SALT,
            info = info,
        ).derive(shared_key)

        return encryption_key



#def onion_encrypt(client, message): 

#def initiate_conection(client_2):

if __name__ == "__main__":
    client_1 = Client()
    client_2 = Client()


    #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #sock.connect(port)

    shared1 = client_1.shared_secret(client_2.public_key)
    shared2 = client_2.shared_secret(client_1.public_key)

    df_client_1 = client_1.diffie_hellman(client_2.public_key)
    df_client_2 = client_2.diffie_hellman(client_1.public_key)
    assert df_client_1 == df_client_2
    
    #sock.send(onion_message)
    #esponse = sock.recv(4096)