# Dead Drop

import os
from config import GLOBAL_MESSAGE_LEN, NUM_BUCKETS

# Buckets in dead drop
def get_bucket_index(dead_drop_hash):
    # Returns index of bucket for this message
    hash_to_int = int.from_bytes(dead_drop_hash, byteorder='big')
    bucket_id = hash_to_int % NUM_BUCKETS
    print("\n\n\n\n\nDead Drop Hash: ")
    print(dead_drop_hash)
    print("\n\n\n\nBucket ID: ")
    print(bucket_id)
    return bucket_id

# Use dead drop to swap locations of the messages with the same bucket id
def dead_drop_swap(message_list):
    user_buckets = {}
    output = [None] * len(message_list)

    # Separate hash and message
    for i, message in enumerate(message_list):
        dead_drop_hash = message[:16]                      # first 32 bytes of message is the hash of the dead drop index
    
        bucket_id = get_bucket_index(dead_drop_hash)

        # If there is a message in the bucket, swap
        if bucket_id in user_buckets:
            match_index, match_message = user_buckets.pop(bucket_id)
            print("\n\nThese messages should match: ")
            print(match_message)
            print(message)
            print("\n\n\n")
            print("Bucket ID: ")
            print(bucket_id)
            print("\n\n\n\n")
            output[i] = match_message
            output[match_index] = message

        # If no messages are in the bucket, insert
        else:
            print("\n\n\n\nNo messages in bucket\n\n\n\n")
            user_buckets[bucket_id] = (i, message)
        
    # If there are buckets which did not swap, fill with dummy messages
    for bucket_id, (y, msg) in user_buckets.items():
        output[y] = msg

    return output