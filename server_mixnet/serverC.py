

def setupC():
    global NUM_BUCKETS 
    NUM_BUCKETS = 100

# Buckets in dead drop
def get_bucket_index(dead_drop_hash):
    # Returns index of bucket for this message
    hash_to_int = int.from_bytes(dead_drop_hash, byteorder='big')
    bucket_id = hash_to_int % NUM_BUCKETS
    return bucket_id

# Use dead drop to swap locations of the messages with the same shared keys

def dead_drop_swap(bucket_id):
    dead_drop_hash = message[0:32]                      # first 32 bytes of message is the hash of the dead drop index
    encrypted_message = message[32:]                    # rest of the message is the encrypted content     
    dead_drop.insert(bucket_id, encrypted_message)
    return dead_drop