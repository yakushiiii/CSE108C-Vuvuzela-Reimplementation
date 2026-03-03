from keys import serverB_private_key
from encryption import decrypt_private_key
from shuffle import shuffle
from config import ROUND_NUM

# Decrypts first layer of encryption using server B's private key
def serverB_decrypt(messages_listA):
    for messages in messages_listA:
        decrypted_messages_listB = decrypt_private_key(serverB_private_key, messages)
    return decrypted_messages_listB

# Shuffles the messages in messages_list using permutation
def serverB_shuffle(serverA_messages_list):
    serverB_shuffled_messages, i = shuffle(serverA_messages_list)
    serverB_permutations = i 
    return serverB_shuffled_messages, serverB_permutations


serverB_permutations = []

## SEND TO CLIENT
# Unshuffles the messages in messages_list using inverse permutation
def serverB_unshuffle(serverB_unshuffled_messages):
    serverA_unshuffled_messages = unshuffle(serverB_unshuffled_messages, serverA_permutations_dictionary)