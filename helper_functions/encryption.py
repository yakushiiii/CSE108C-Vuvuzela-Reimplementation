# Helper Functions for Encryption
from cryptography.hazamat.primitives.asymmetric import rsa, padding
from cryptography.hazamat.primitives import serialization, hashes
from cryptography.hazamat.primitives import default_backend

# Decrypt Private Key
def decrypt_private_key(private_key, ciphertext: bytes) -> str:
    decrypted_ciphertext = private_key.decrypt(ciphertext, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)).decode("utf-8")
    return decrypted_ciphertext