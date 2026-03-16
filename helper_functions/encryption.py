# Helper Functions for Encryption
import socket 
import asyncio 
import os
import hashlib
import struct
import json
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import config
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

# Note:
# Instead of raw Diffie Hellman like outlined in the paper, to ensure each key/shared secret is uniformly random enough we chose to use HKDF to derive the raw diffie hellman key

# ---------------------------
# Client Encryption Functions
# ---------------------------

"""
#creating a shared secret
def shared_secret(self_private_key, other_public_key):
    shared_key = self_private_key.exchange(other_public_key)
    return shared_key
"""

def generate_key_pair():
    private_key = x25519.X25519PrivateKey.generate()
    public_key = private_key.public_key()

    return private_key, public_key

#creating a shared secret
#paper only specifies regular diffie hellman which is just the key exchange, however we use HKDF because it gaurauntees the key to be uniformly random enough
def shared_secret(self_private_key, other_public_key):
    info = b"first-layer-encryption"
    shared_key = self_private_key.exchange(other_public_key)

    encryption_key = HKDF(
        algorithm = hashes.SHA256(),
        length = config.GLOBAL_KEY_LEN,
        salt = config.GLOBAL_SALT,
        info = info,
    ).derive(shared_key)
    return encryption_key

#for client encryption of actual plaintext message
def encrypt_message(encryption_key, message, round_number): #add round num later
    #for further security we pad all messages to be the same length
    if len(message) > config.GLOBAL_MESSAGE_LEN:
        raise ValueError("WARNING: The message is too long.")
    message = message.encode()
    padded_message = message + b"\00" * (config.GLOBAL_MESSAGE_LEN - len(message))
    #have to create a nonce, in the paper they use the round number
    #for now lets use a fixed value
    nonce = round_number.to_bytes(12, "big")
    aesgcm = AESGCM(encryption_key)
    ciphertext = aesgcm.encrypt(nonce, padded_message, None)
    return ciphertext

def get_dead_drop_id(shared_secret, round_number):
    round_bytes = round_number.to_bytes(8, "big")
    dead_drop_id = hashlib.sha256(shared_secret + round_bytes).digest()
    return dead_drop_id[:16] #Vuvuzela uses 128-bit dead drop IDs

def layer_encryption(server_public_key, payload, cl_eph_priv_key, cl_eph_pub_key, round_number):
    info = b'onion-layer-encryption'
    sh_key = cl_eph_priv_key.exchange(server_public_key)
    key = HKDF(
        algorithm = hashes.SHA256(),
        length = config.GLOBAL_KEY_LEN,
        salt = config.GLOBAL_SALT,
        info = info,
    ).derive(sh_key)

    aesgcm = AESGCM(key)
    nonce = round_number.to_bytes(12, "big")
    ciphertext = aesgcm.encrypt(nonce, payload, None)

    client_epubk_bytes = cl_eph_pub_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

    header = struct.pack("!32sI", client_epubk_bytes, len(ciphertext))
    return header + ciphertext, key

#generate ephemeral client keys for every round
#let's assume that the client already has all the server public keys in a directory json filesince they are long term keys
def onion_encrypt(round_number, encryption_key, message, dead_drop_id, serverA_public_key, serverB_public_key, serverC_public_key): 
    cl_eph_priv_keys = []
    cl_eph_pub_keys = []
    for i in range(3):
        cl_eph_private_key, cl_eph_public_key = generate_key_pair()
        cl_eph_priv_keys.append(cl_eph_private_key)
        cl_eph_pub_keys.append(cl_eph_public_key)

    server_client_sh_keys = [None] * 3

    ciphertext = encrypt_message(encryption_key, message, round_number)
    payload_header = struct.pack("!16sI", dead_drop_id, len(ciphertext))

    inner, inner_key = layer_encryption(serverC_public_key, payload_header + ciphertext, cl_eph_priv_keys[0], cl_eph_pub_keys[0], round_number)
    middle, middle_key = layer_encryption(serverB_public_key, inner, cl_eph_priv_keys[1], cl_eph_pub_keys[1], round_number)
    outer, outer_key = layer_encryption(serverA_public_key, middle, cl_eph_priv_keys[2], cl_eph_pub_keys[2], round_number)
 
    server_client_sh_keys[0] = outer_key
    server_client_sh_keys[1] = middle_key
    server_client_sh_keys[2] = inner_key

    return outer, server_client_sh_keys

def onion_decrypt(server_client_sh_keys, onion_message, partner_shared_secret, round_number):
    #because of the way we need to receive sockets first struct should already be unpacked
    round_number = round_number.to_bytes(12, "big")
    aesgcm_cipher = AESGCM(server_client_sh_keys[0])
    payload = aesgcm_cipher.decrypt(round_number, onion_message, None)
    #now doing the rest of the lyares
    for i in range(2):
        cipher_len = struct.unpack("!I", payload[:4])[0] 
        ciphertext = payload[4:4+cipher_len]
        aesgcm_cipher = AESGCM(server_client_sh_keys[i+1])
        payload = aesgcm_cipher.decrypt(round_number, ciphertext, None)

    #now decrypting the final inside layer
    #if struct unpack error then dummy message
    try: 
        _, cipher_len = struct.unpack("!16sI", payload[:20])
    except struct.error:
        return None
    ciphertext = payload[20:20+cipher_len]
    aesgcm_cipher = AESGCM(partner_shared_secret)
    payload = aesgcm_cipher.decrypt(round_number, ciphertext, None)
    return payload

# ---------------------------
# Server Encryption Functions
# ---------------------------

#from server A -> server C
def server_layer_decryption(server_private_key, payload, round_number):
    client_pubkey_bytes, cipher_len = struct.unpack("!32sI", payload[:36]) 
    ciphertext = payload[36:36+cipher_len]
    cl_public_key = x25519.X25519PublicKey.from_public_bytes(client_pubkey_bytes)   
    info = b'onion-layer-encryption'
    sh_key = server_private_key.exchange(cl_public_key)
    key = HKDF(
        algorithm = hashes.SHA256(),
        length = config.GLOBAL_KEY_LEN,
        salt = config.GLOBAL_SALT,
        info = info,
    ).derive(sh_key)

    aesgcm = AESGCM(key)
    nonce = round_number.to_bytes(12, "big")
    ciphertext = aesgcm.decrypt(nonce, ciphertext, None)
    #need to save this key for the way back.
    return ciphertext, key

#from server C -> server A
def server_layer_encryption(shared_key, payload, round_number):
    aesgcm = AESGCM(shared_key)
    nonce = round_number.to_bytes(12, "big")
    ciphertext = aesgcm.encrypt(nonce, payload, None)
    ciphertext_header = struct.pack("!I", len(ciphertext))
    return ciphertext_header + ciphertext


