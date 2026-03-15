# Server A, B, C
# Keys[private, public]
from encryption import generate_key_pair
from config import NUMBER_NODES

keys = []
for i in range(len(NUMBER_NODES)):
    priv, pub = generate_key_pair()
    keys.append([priv, pub])

serverA_public_key = keys[0][1]
serverB_public_key = keys[1][1]
serverC_public_key = keys[2][1]