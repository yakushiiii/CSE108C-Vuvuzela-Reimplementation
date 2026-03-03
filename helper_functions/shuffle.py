import random
import secrets
from init import permutations_dictionary
from config import ROUND_NUM

# Shuffle messages in list and return shuffled message and indices
def shuffle(messages_list):
    i = list(range(len(messages_list)))                 # Create list of indices
    secrets.SystemRandom().shuffle(i)                   # Shuffle the indices to create a random permutation
    shuffled_messages = []                             # Create empty list to store shuffled messages

    for n in i:                                        # Reorder messages using shuffled indices
        shuffled_messages.append(messages_list[n])           # Stores permutation and shuffle for server A
    return shuffled_messages, i

# Unshuffle messages using stored permutation and return message
def unshuffle(shuffled_messages, permutations_dictionary):
    try: 
        unshuffled_messages = [] * len(shuffled_messages)    # Create empty list to store unshuffled messages
        permutation = permutations_dictionary[ROUND_NUM]
        i = 0
        for n in permutation:
            unshuffled_messages[n] = shuffled_messages[i]    # Unshuffle messages using stored permutation
            i += 1
        return unshuffled_messages
    except:
        print("Error: function unshuffle() is not working for some reason")
