import random
from main import permutations_dictionary

def shuffle(messages_list):
    i = list(range(len(messages_list)))                 # Create list of indices
    random.shuffle(i)                                   # Shuffle the indices to create a random permutation

    for n in i:                                         # Reorder messages using shuffled indices
        shuffled_messages = messages_list[n]            # Stores permutation and shuffle for server A
    return shuffled_messages, i

def unshuffle(shuffled_messages, permutations_dictionary):
    