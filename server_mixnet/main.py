from serverA import setupA, receive_messages_from_client, serverA_decrypt, serverA_shuffle, serverA_unshuffle
from serverB import serverB_decrypt, serverB_shuffle, serverB_unshuffle
from serverC import serverC_decrypt, serverC_shuffle, serverC_unshuffle, get_bucket_index, dead_drop_swap
from config import BATCHING
from shuffle import shuffle, unshuffle
from encryption import server_decrypt, server_encrypt
from keys import serverA_private_key, serverB_private_key, serverC_private_key, serverA_public_key, serverB_public_key, serverC_public_key

def main():
    global serverA_permutations, serverB_permutations, serverC_permutations
    serverA_permutations = []
    serverB_permutations = []
    serverC_permutations = []
    try: 
        # Server A receives messages from client, decrypts them, and shuffles them
        try:
            setupA()
            new_messages_list = receive_messages_from_client(BATCHING)
            decrypted_message_listA = server_decrypt(serverA_private_key, new_messages_list)
            shuffled_messages_listA, serverA_permutations = shuffle(decrypted_message_listA)
        except:
            print("Error in server A")

        # Server B receives shuffled messages from server A, decrypts them, and shuffles them
        try:
            decrypted_message_listB = server_decrypt(serverB_private_key, shuffled_messages_listA)
            shuffled_messages_listB, serverB_permutations = shuffle(decrypted_message_listB)
        except:
            print("Error in server B")

        # Server C receives shuffled messages from server B, decrypts them, shuffles them, and swaps dead drop locations before unshuffling and re-encrypting them
        try:
            decrypted_message_listC = server_decrypt(serverC_private_key, shuffled_messages_listB)
            shuffled_messages_listC, serverC_permutations = shuffle(decrypted_message_listC)
            dead_drop = dead_drop_swap()
            unshuffled_messages_listC = unshuffle(shuffled_messages_listC, serverC_permutations)
            output_messages_listC = server_encrypt(serverC_public_key, unshuffled_messages_listC)
        except:
            print("Error in server C")

        # Server B receives messages from server C, unshuffles them, and re-encrypts them before sending them to server A
        try:
            unshuffled_messages_listB = unshuffle(output_messages_listC, serverB_permutations)
            output_messages_listB = server_encrypt(serverB_public_key, unshuffled_messages_listB)
        except:
            print("Error in server B unshuffle")

        # Server A receives messages from server B, unshuffles them, re-encrypts them, and sends them to the client
        try:
            unshuffled_messages_listA = unshuffle(output_messages_listB, serverA_permutations)
            output_messages_listA = server_encrypt(serverA_public_key, unshuffled_messages_listA)
        except:
            print("Error in server A unshuffle")

    except:
        print("Error running main")