from keys import serverB_private_key
from encryption import decrypt_private_key
from shuffle import shuffle
from config import ROUND_NUM

# Decrypts first layer of encryption using server B's private key
def serverB_decrypt(messages_list):
    for messages in messages_list:
        messages_list1 = decrypt_private_key(serverB_private_key, messages)

# Shuffles the messages in messages_list using permutation
def serverA_shuffle(messages_list):
    serverA_shuffled_messages, i = shuffle(messages_list)
    serverB_permutations_dictionary[ROUND_NUM] = i 


serverB_permutations_dictionary = {} 