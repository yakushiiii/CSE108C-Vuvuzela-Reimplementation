# Shuffle

import secrets

# Shuffle messages in list and return shuffled message and indices
def shuffle(messages_list):
    try:
        index = list(range(len(messages_list)))                 # Create list of indices
        secrets.SystemRandom().shuffle(index)                   # Shuffle the indices to create a random permutation
        shuffled_messages = []                             # Create empty list to store shuffled messages

        for n in index:                                        # Reorder messages using shuffled indices
            shuffled_messages.append(messages_list[n])           # Stores permutation and shuffle for server A
        return shuffled_messages, index
    except:
        print("Error: Shuffle not working")

# Unshuffle messages using stored permutation and return message
def unshuffle(shuffled_messages, permutations):
    try: 
        unshuffled_messages = [None] * len(shuffled_messages)    # Create empty list to store unshuffled messages
        i = 0
        for i, original_i in enumerate(permutations):
            unshuffled_messages[original_i] = shuffled_messages[i]    # Unshuffle messages using stored permutation
        return unshuffled_messages
    except:
        print("Error: function unshuffle() is not working for some reason")
