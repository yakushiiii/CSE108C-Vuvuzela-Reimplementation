from keys import serverB_private_key
from encryption import decrypt_private_key

# Decrypts first layer of encryption using server C's private key
def serverB_decrypt(messages_list):
    for messages in messages_list:
        messages_list1 = decrypt_private_key(serverB_private_key, messages)

# Use dead drop to swap locations of the messages with the same shared keys