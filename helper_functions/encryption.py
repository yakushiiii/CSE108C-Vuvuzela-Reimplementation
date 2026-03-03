# Helper Functions for Encryption
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