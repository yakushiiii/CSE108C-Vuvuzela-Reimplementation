from serverA import handle_client, batching, broadcast, server_A
from serverB import serverB_decrypt, serverB_shuffle, serverB_unshuffle
from serverC import serverC_decrypt, serverC_shuffle, serverC_unshuffle, get_bucket_index, dead_drop_swap
from config import BATCHING, Rounds, NUM_BUCKETS
from shuffle import shuffle, unshuffle
from encryption import server_decrypt, server_encrypt, reencrypt_server
from keys import serverA_private_key, serverB_private_key, serverC_private_key, serverA_public_key, serverB_public_key, serverC_public_key
import asyncio

async def init_rounds():
    rounds = Rounds()
    message_list = await server_A(rounds)