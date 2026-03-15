# Server Class Node

import socket, sleep, threading
from serverC import dead_drop_swap
from shuffle import shuffle, unshuffle
from keys import keys
from encryption import server_layer_encryption, server_layer_decryption, shared_secret
import pickle, time

clients = set()
clients_lock = threading.Lock()
global round_number 
round_number = 1
client_messages = {}

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

class Node:
    PORT_START = 6001

    def __init__(self, node_id, prev_node=None, next_node=None):
        self.id = node_id
        self.port = self.PORT_START + node_id
        self.prev_node = prev_node
        self.next_node = next_node
        self.private_key = keys[node_id][0]
        self.host = "127.0.0.1"
        self.pub_key = []
        self.permutations = []
        print("Done initializing Nodes")

    # First Server
    def handle_client(self, conn: socket.socket, addr):
        try:
            # First Server 
            if not self.prev_node:
            
                with clients_lock:
                    client_messages[conn] = None

                while True:
                    try:
                        data = conn.recv(4096)
                        print("Received data from client")
                        if not data:
                            print("received no data from client")
                            break
                        with clients_lock:
                            client_messages[conn] = data
                            print("added data")
                    except Exception as e:
                        print(f"Client Error: {e}")
                        break
                    finally:
                        with clients_lock:
                            client_messages.pop(conn, None)
                        conn.close()
                        print(f"Client disconnected: {addr}")
        except Exception as e:
            print(f"Client Error: {e}")

    # Batching for First Server
    def batching(self, BATCHING):

        batching_message = {
            "type": "START_SEND",
            "round_number": round_number  
        }

        batching_string = pickle.dumps(batching_message)
        batching_bytes = batching_string.encode()

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
                receive_string = pickle.dumps(receive_message)
                receive_bytes = receive_string.encode()
                broadcast(receive_bytes)
                
            if not batch_list:
                continue
            
            pub_key = []
            dcipher = []
            for msg in batch_list:
                pub_key.append(msg[:32])
                decrypted_cipher = server_layer_decryption(self.private_key, msg[32:])
                dcipher.append(decrypted_cipher)
            
            shuffled, node0_perm = shuffle(dcipher)

            # Forward decrypted data to next node
            if self.next_node:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((self.host, self.next_node.port))

                    payload = pickle.dumps(shuffled).encode()
                    s.sendall(payload)

                    # Wait for response
                    response_data = s.recv(4096)
                    returned_batch = pickle.loads(response_data.decode())

                    # Re-encrypt batch
                    encrypted_batch = []
                    i = 0
                    for msg in returned_batch:
                        shared_key = shared_secret(self.private_key, pub_key[i])
                        encrypted_message = server_layer_encryption(shared_key, msg, round_number)
                        encrypted_batch.append(encrypted_message)
                        i += 1
                    
                    # Unshuffle batch
                    unshuffled_batch = unshuffle(encrypted_batch, node0_perm)

                    # Send batch back to clients
                    for i in range(len(conn_list)):
                        try:
                            conn_list[i].sendall(unshuffled_batch[i].encode())
                        except:
                            print("Error sending back to clients from node")
                    print(f"Round {round_number} complete.  Incrementing")
                    round_number += 1

                    # Clear public keys for current node
                    self.pub_key = []
                    # Broadcast round completion
                    broadcast(b"Round Complete")

    # Nodes > 0
    def handle_server(self, conn, addr):

        # Receive batch from other server
        try:
            data = conn.recv(4096)
            if not data:
                return
            batch_list = pickle.loads(data.decode())

            # Decrypt batch
            dcipher = []
            for msg in batch_list:
                self.pub_key.append(msg[:32])
                decrypted_cipher = server_layer_decryption(self.private_key, msg[32:])
                dcipher.append(decrypted_cipher)

            # Shuffle Batch
            shuffled_batch, self.permutations = shuffle(dcipher)

            # If not last node, send
            if self.next_node:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((self.host, self.next_node.port))
                    print("connected to next node")
                    s.sendall(pickle.dumps(shuffled_batch).encode())
                    print("Data Forwarded")
                    
                    # Get response from next node
                    response_data = s.recv(4096)
                    returned_batch = pickle.loads(response_data.decode())

                    # Unshuffle response
                    unshuffled_batch, self.permutations = unshuffle(returned_batch)
                    
                    # Re-encrypt batch
                    encrypted_batch = []
                    i = 0
                    for msg in unshuffled_batch:
                        shared_key = shared_secret(self.private_key, self.pub_key[i])
                        encrypted_message = server_layer_encryption(shared_key, msg, round_number)
                        encrypted_batch.append(encrypted_message)
                        i += 1

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((self.host, self.prev_node.port))
                    print("connected to prev node")
                    s.sendall(pickle.dumps(encrypted_batch).encode())
                    print("Data Forwarded")
                    # Clear public keys for current node
                    self.pub_key = []
            
            # Last Node
            else:
                # Shuffle and Swap
                swap = dead_drop_swap(shuffled_batch)
                unshuffled_batch = unshuffle(swap, self.permutations)
                
                # Re-encrypt batch
                encrypted_batch = []
                i = 0
                for msg in unshuffled_batch:
                    shared_key = shared_secret(self.private_key, self.pub_key[i])
                    encrypted_message = server_layer_encryption(shared_key, msg, round_number)
                    encrypted_batch.append(encrypted_message)
                    i += 1

                # Send encrypted batch
                conn.sendall(pickle.dumps(encrypted_batch).encode())
                # Clear public keys for current node
                self.pub_key = []

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

                