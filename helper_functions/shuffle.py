import random
from main import permutations_dictionary
from config import ROUND_NUM

# Shuffle messages in list and return shuffled message and indices
def shuffle(messages_list):
    i = list(range(len(messages_list)))                 # Create list of indices
    random.shuffle(i)                                   # Shuffle the indices to create a random permutation

    for n in i:                                         # Reorder messages using shuffled indices
        shuffled_messages = messages_list[n]            # Stores permutation and shuffle for server A
    return shuffled_messages, i

# Unshuffle messages using stored permutation and return message
def unshuffle(shuffled_messages, serverA_permutations_dictionary):
    try: 
        permutation = serverA_permutations_dictionary[ROUND_NUM]
    except:
        print("Error: function unshuffle() is not working for some reason")
