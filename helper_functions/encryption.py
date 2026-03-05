# Helper Functions for Encryption
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
from cryptography.hazamat.primitives.asymmetric import rsa, padding
from cryptography.hazamat.primitives import serialization, hashes
from cryptography.hazamat.primitives import default_backend

# Decrypt Private Key
def decrypt_private_key(private_key, ciphertext: bytes) -> str:
    decrypted_ciphertext = private_key.decrypt(ciphertext, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)).decode("utf-8")
    return decrypted_ciphertext

def server_decrypt(private_key, new_messages_list):
    decrypted_message_list = []
    for messages in new_messages_list:
        decrypted_message_list.append(decrypt_private_key(private_key, messages))
    return decrypted_message_list

# Encrypt Public Key
def encrypt_public_key(public_key, text: str) -> bytes:
    ciphertext = public_key.encrypt(text.encode("utf-8"), padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    return ciphertext

def server_encrypt(public_key, message_list):
    encrypted_message_list = []
    for message in message_list:
        encrypted_message_list.append(encrypt_public_key(public_key, message))
    return encrypted_message_list

#creating a shared secret
def shared_secret(self_private_key, other_public_key):
    shared_key = self_private_key.exchange(other_public_key)
    return shared_key

def diffie_hellman(self_private_key, other_public_key):
    info = b"first-layer-encryption"
    shared_key = self_private_key.exchange(other_public_key)

    encryption_key = HKDF(
        algorithm = hashes.SHA256(),
        length = config.GLOBAL_KEY_LEN,
        salt = config.GLOBAL_SALT,
        info = info,
    ).derive(shared_key)
    return encryption_key

def encrypt_message(encryption_key, message, round_number): #add round num later
    #for further security we pad all messages to be the same length
    if len(message) > config.GLOBAL_MESSAGE_LEN:
        raise ValueError("WARNING: The message is too long.")
    padded_message = message + b"\00" * (100 - len(message))

    #have to create a nonce, in the paper they use the round number
    #for now lets use a fixed value
    nonce = round_number.to_bytes(12, "big")
    aesgcm = AESGCM(encryption_key)
    ciphertext = aesgcm.encrypt(nonce, padded_message)
    return ciphertext

def decrypt_message(round_number, encryption_key, ciphertext): #add round num later
    aesgcm = AESGCM(encryption_key)
    nonce = round_number.to_bytes(12, "big") #hardcode the nonce for now
    plaintext = aesgcm.decrypt(nonce, ciphertext)
    return plaintext

def get_dead_drop_id(shared_secret, round_number):
    round_bytes = round_number.to_bytes(8, "big")
    dead_drop_id = hashlib.sha256(shared_secret + round_bytes).digest()
    return dead_drop_id[:16] #Vuvuzela uses 128-bit dead drop IDs

def layer_encryption(round_number, server_public_key, payload):
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

def onion_encrypt(round_number, ciphertext, dead_drop_id, serverA_public_key=serverA_public_key, serverB_public_key=serverB_public_key, serverC_public_key=serverC_public_key): 
    inner = layer_encryption(round_number, serverC_public_key, dead_drop_id + ciphertext)
    middle = layer_encryption(round_number, serverB_public_key, inner)
    outer = layer_encryption(round_number, serverA_public_key, middle)
 
    return outer