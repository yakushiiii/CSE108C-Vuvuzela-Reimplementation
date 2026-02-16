import random
from main import permutations_dictionary
from config import ROUND_NUM

def shuffle(messages_list):
    i = list(range(len(messages_list)))                 # Create list of indices
    random.shuffle(i)                                   # Shuffle the indices to create a random permutation

    for n in i:                                         # Reorder messages using shuffled indices
        shuffled_messages = messages_list[n]
        permutations_dictionary[ROUND_NUM] = i
    return shuffled_messages, i                         # Stores permutation and sender's temporary public key for server A

def unshuffle(shuffled_messages, permutations_dictionary):
    