# Server Class Node

import socket, threading
from dead_drop import dead_drop_swap
from shuffle import shuffle, unshuffle
from keys import keys
from encryption import server_layer_encryption, server_layer_decryption
import pickle, time

clients = set()
clients_lock = threading.Lock()
round_number_lock = threading.Lock()
round_number = 1
client_messages = {}

# Broadcast
def broadcast(message: bytes):
    dead = []
    with clients_lock:
        for conn in clients:
            try:
                conn.sendall(message)
            except OSError:
                dead.append(conn)

        for conn in dead:
            clients.remove(conn)
            conn.close()

# Server Class
class Node:
    PORT_START = 6001

    def __init__(self, node_id, prev_node=None, next_node=None):
        self.id = node_id
        self.port = self.PORT_START + node_id
        self.prev_node = prev_node
        self.next_node = next_node
        self.private_key = keys[node_id][0]
        self.host = "127.0.0.1"
        self.sh_key = []
        self.permutations = []
        self._lock = threading.Lock()
        print("Done initializing Nodes")

    # First Server
    def handle_client(self, conn: socket.socket, addr):
        try:
            # First Server 
            with clients_lock:
                clients.add(conn)
                client_messages[conn] = None

            while True:
                try:
                    data = conn.recv(4096)
                    print("Received data from client")
                    if not data:
                        print(f"received no data from {addr}")
                        break
                    with clients_lock:
                        client_messages[conn] = data
                        print("added data")
                except Exception as e:
                    print(f"Client Error: {e}")
                    break
        except Exception as e:
            print(f"Client Error: {e}")

    # Batching for First Server
    def batching(self, BATCHING):
        global round_number

        batching_message = {
            "type": "START_SEND",
            "round_number": round_number  
        }

        batching_bytes = pickle.dumps(batching_message)

        while True:
            broadcast(batching_bytes)
            time.sleep(BATCHING)
            batch_list = []
            conn_list = []

            with clients_lock:
                for conn, msg in client_messages.items():
                    conn_list.append(conn)
                    batch_list.append(msg)
                    client_messages[conn] = None

                # Broadcast to clients to begin expecting messages
                receive_message = {
                    "type": "START_RECEIVE", 
                }
                receive_bytes = pickle.dumps(receive_message)
                broadcast(receive_bytes)
                
            if not batch_list:
                continue
            
            sh_key = []
            dcipher = []
            for msg in batch_list:
                decrypted_cipher, key = server_layer_decryption(self.private_key, msg, round_number)
                dcipher.append(decrypted_cipher)
                sh_key.append(key)
            
            shuffled, node0_perm = shuffle(dcipher, self.permutations)

            # Forward decrypted data to next node
            if self.next_node:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((self.host, self.next_node.port))

                    payload = pickle.dumps(shuffled)
                    s.sendall(payload)

                    # Wait for response
                    response_data = s.recv(4096)
                    returned_batch = pickle.loads(response_data)

                    # Re-encrypt batch
                    encrypted_batch = []
                    i = 0
                    for msg in returned_batch:
                        encrypted_message = server_layer_encryption(self.sh_key[i], msg, round_number)
                        encrypted_batch.append(encrypted_message)
                        i += 1
                    
                    # Unshuffle batch
                    unshuffled_batch = unshuffle(encrypted_batch, node0_perm)
                    self.permutations = []

                    # Send batch back to clients
                    for conn, reply in zip(conn_list, unshuffled_batch):
                        try:
                            conn.sendall(reply)
                        except:
                            print("Error sending back to clients from node")
                    print(f"Round {round_number} complete.  Incrementing")
                    with round_number_lock:
                        round_number += 1

                    # Clear public keys for current node
                    self.sh_key = []
                    # Broadcast round completion
                    broadcast(b"Round Complete")

    # Nodes > 0
    def handle_server(self, conn, addr):

        # Receive batch from other server
        try:
            data = conn.recv(4096)
            if not data:
                return
            batch_list = pickle.loads(data)

            # Decrypt batch
            dcipher = []
            sh_key = []
            for msg in batch_list:
                decrypted_cipher, key = server_layer_decryption(self.private_key, msg, round_number)
                dcipher.append(decrypted_cipher)
                sh_key.append(key)

            # Shuffle Batch
            shuffled_batch, self.permutations = shuffle(dcipher)

            # If not last node, send
            if self.next_node:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((self.host, self.next_node.port))
                    print("connected to next node")
                    s.sendall(pickle.dumps(shuffled_batch))
                    print("Data Forwarded")
                    
                    # Get response from next node
                    response_data = s.recv(4096)
                    returned_batch = pickle.loads(response_data)

                    # Unshuffle response
                    unshuffled_batch, self.permutations = unshuffle(returned_batch, self.permutations)
                    self.permutations = []
                    
                    # Re-encrypt batch
                    encrypted_batch = []
                    i = 0
                    for msg in unshuffled_batch:
                        encrypted_message = server_layer_encryption(self.sh_key[i], msg, round_number)
                        encrypted_batch.append(encrypted_message)
                        i += 1

                    s.sendall(pickle.dumps(encrypted_batch))
                    print("Data Forwarded")
                    # Clear public keys for current node
                    self.sh_key = []
            
            # Last Node
            else:
                # Shuffle and Swap
                swap = dead_drop_swap(shuffled_batch)
                unshuffled_batch = unshuffle(swap, self.permutations)
                self.permutations = []
                
                # Re-encrypt batch
                encrypted_batch = []
                i = 0
                for msg in unshuffled_batch:
                    encrypted_message = server_layer_encryption(self.sh_key, msg, round_number)
                    encrypted_batch.append(encrypted_message)
                    i += 1

                # Send encrypted batch
                conn.sendall(pickle.dumps(encrypted_batch))
                # Clear public keys for current node
                self.sh_key = []

        except Exception as e:
            print(f"Node {self.id} Error: {e}")
        finally:
            conn.close()

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", self.port))
            s.listen()
            print(f"Node {self.id} listening on port {self.port}")

            while True:
                conn, addr = s.accept()
                if self.id == 0:
                    t = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                else:
                    t = threading.Thread(target=self.handle_server, args=(conn, addr), daemon=True)
                t.start()

                