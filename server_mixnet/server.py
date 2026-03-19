# Server Class Node

import socket, threading
from server_mixnet import dead_drop
from helper_functions import shuffle, encryption
from keys import keys
import pickle, time, struct, json, os

clients = set()
clients_lock = threading.Lock()
round_number_lock = threading.Lock()
round_number = 1
client_messages = {}
next_client_id = 0
next_client_id_lock = threading.Lock()
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DIRECTORY_PATH = os.path.join(BASE_DIR, "directory.json")


# Broadcast
def broadcast(message: bytes):
    dead = []
    with clients_lock:
        for conn in clients:
            try:
                send_client_packet(conn, message)
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
        self.host = "169.233.123.148" #CHANGE
        self.sh_key = []
        self.permutations = []
        self._lock = threading.Lock()
        print("Done initializing Nodes")

    # First Server
    def handle_client(self, conn: socket.socket, addr):
        print(f"SERVER: entered handle_client for {addr}")
        
        try:
            # First Server 

            while True:
                try:
                    print("SERVER: waiting for packet")
                    data = recv_packet(conn)

                    if not data:
                        break

                    try:
                        print("SERVER: decoding packet")
                        payload = json.loads(data.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        with clients_lock:
                            client_messages[conn] = data
                            print("added onion packet")
                            continue
                    if payload.get("type") == "USERNAME_REQUEST":
                        print(f"Username Request from {addr}")

                        global next_client_id
                        with next_client_id_lock:
                            username = "client" + str(next_client_id)
                            next_client_id += 1
                            
                        with open(DIRECTORY_PATH, "r") as f:
                            directory = json.load(f)

                        if "users" not in directory:
                            directory["users"] = {}

                        directory["users"][username] = {
                            "public_key": payload["public_key"]
                        }

                        with open(DIRECTORY_PATH, "w") as f:
                            json.dump(directory, f, indent=4)

                        user_msg = {
                            "type": "USERNAME",
                            "username": username,
                        }
                        msg = json.dumps(user_msg).encode("utf-8")
                        send_client_packet(conn, msg)
                        with clients_lock:
                            clients.add(conn)
                            client_messages[conn] = None

                    else:
                        print("SERVER: ignoring unknown JSON packet")
                except Exception as e:
                    print(f"SERVER: JSON/control handling error: {type(e).__name__}: {e}")
        except Exception as e:
            print(f"Client Error outer: {e}")

    # Batching for First Server
    def batching(self, BATCHING):
        global round_number

        while True:

            time.sleep(2)

            batching_message = {
                "type": "START_SEND",
                "round_number": round_number  
            }

            batching_bytes = json.dumps(batching_message).encode("utf-8")
            print("Batching Start Send")

            broadcast(batching_bytes)
            time.sleep(BATCHING)
            batch_list = []
            conn_list = []

            with clients_lock:
                for conn, msg in client_messages.items():
                    if msg is None:
                        continue
                    conn_list.append(conn)
                    batch_list.append(msg)
                    client_messages[conn] = None
            
            if not batch_list:
                continue

            receive_message = {
                "type": "START_RECEIVE",
            }
            receive_bytes = json.dumps(receive_message).encode("utf-8")
            broadcast(receive_bytes)
            print("Start Receive")
                
            
            self.sh_key = []
            dcipher = []
            for msg in batch_list:
                decrypted_cipher, key = encryption.server_layer_decryption(self.private_key, msg, round_number)
                dcipher.append(decrypted_cipher)
                self.sh_key.append(key)
            
            shuffled, self.permutations = shuffle.shuffle(dcipher)

            # Forward decrypted data to next node
            if self.next_node:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((self.host, self.next_node.port))

                    send_server_packet(s, shuffled)
                    print("Sent to Next Node")

                    # Wait for response
                    returned_batch = recv_server_packet(s)
                    print(f"\nNext Node Received Data: ")
                    #print(returned_batch)

                    # Unshuffle batch
                    unshuffled_batch = shuffle.unshuffle(returned_batch, self.permutations)
                    self.permutations = []
                    print("\nUnshuffled Batch: ")
                    #print(unshuffled_batch)

                    # Re-encrypt batch
                    encrypted_batch = []
                    i = 0
                    for msg in unshuffled_batch:
                        encrypted_message = encryption.server_layer_encryption(self.sh_key[i], msg, round_number)
                        encrypted_batch.append(encrypted_message)
                        i += 1
                    print("\nRe-encrypted Batch: ")
                    #print(encrypted_batch)

                    # Send batch back to clients
                    for conn, reply in zip(conn_list, encrypted_batch):
                        try:
                            send_client_packet(conn, reply)
                            print(f"Sent back to Client {conn}")
                        except:
                            print("Error sending back to clients from node")
                    print(f"Round {round_number} complete.  Incrementing")
                    round_number += 1

                    # Clear public keys for current node
                    self.sh_key = []

                    time.sleep(1)
                    print("Sending Out Directory")
                    with open(DIRECTORY_PATH, "r") as f:
                        pay = json.load(f)

                    payload_bytes = json.dumps(pay).encode("utf-8")
                    for conn in conn_list:
                        send_client_packet(conn, payload_bytes)
                    print(f"Sent Directory")


    # Nodes > 0
    def handle_server(self, conn, addr):

        # Receive batch from other server
        try:
            batch_list = recv_server_packet(conn)

            print("\nData Received from other server")
            #print(batch_list)

            # Decrypt batch
            dcipher = []
            self.sh_key = []
            for msg in batch_list:
                decrypted_cipher, key = encryption.server_layer_decryption(self.private_key, msg, round_number)
                dcipher.append(decrypted_cipher)
                self.sh_key.append(key)

            # Shuffle Batch
            shuffled_batch, self.permutations = shuffle.shuffle(dcipher)

            # If not last node, send
            if self.next_node:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((self.host, self.next_node.port))
                    print("connected to next node")
                    send_server_packet(s, shuffled_batch)
                    print("Data Forwarded")
                    
                    # Get response from next node
                    returned_batch = recv_server_packet(s)

                    print("\nResponse from Node")
                    #print(returned_batch)

                    print("\nNode Permutation: ")
                    #print(self.permutations)

                    # Unshuffle response
                    unshuffled_batch = shuffle.unshuffle(returned_batch, self.permutations)
                    self.permutations = []
                    print("\nUnshuffled Batch: ")
                    #print(unshuffled_batch)
                    
                    # Re-encrypt batch
                    encrypted_batch = []
                    i = 0
                    for msg in unshuffled_batch:
                        encrypted_message = encryption.server_layer_encryption(self.sh_key[i], msg, round_number)
                        encrypted_batch.append(encrypted_message)
                        i += 1
                    print("\nRe-encrypted Batch: ")
                    #print(encrypted_batch)

                    send_server_packet(conn, encrypted_batch)

                    print("Data Forwarded")
                    # Clear public keys for current node
                    self.sh_key = []
            
            # Last Node
            else:
                # Shuffle and Swap
                swap = dead_drop.dead_drop_swap(shuffled_batch)
                print("\nSwapped messages: ")

                unshuffled_batch = shuffle.unshuffle(swap, self.permutations)
                self.permutations = []
                
                # Re-encrypt batch
                encrypted_batch = []
                i = 0
                for msg in unshuffled_batch:
                    encrypted_message = encryption.server_layer_encryption(self.sh_key[i], msg, round_number)
                    encrypted_batch.append(encrypted_message)
                    i += 1
                print("\nRe-encrypted Batch: ")
                #print(encrypted_batch)

                # Send encrypted batch
                send_server_packet(conn, encrypted_batch)
                print("Last Node sent back encrypted batch")
                # Clear public keys for current node
                self.sh_key = []

        except Exception as e:
            print(f"Node {self.id} Error: {e}")
        finally:
            conn.close()

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("169.233.123.148", self.port)) #CHANGE
            s.listen()
            print(f"Node {self.id} listening on port {self.port}")

            while True:
                conn, addr = s.accept()
                print(f"SERVER: accepted connection from {addr}")
                if self.id == 0:
                    print(f"SERVER: starting handler thread for {addr}")
                    t = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                else:
                    t = threading.Thread(target=self.handle_server, args=(conn, addr), daemon=True)
                t.start()


def recv_msg(sock: socket.socket, n: int) -> bytes:
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data

# Client comm
def recv_packet(sock: socket.socket) -> bytes:
    raw_len = recv_msg(sock, 4)
    if not raw_len:
        return None
    data_len = struct.unpack("!I", raw_len)[0]
    return recv_msg(sock, data_len)
            
def send_client_packet(sock: socket.socket, payload: bytes):
    sock.sendall(struct.pack("!I", len(payload)) + payload)

def send_server_packet(sock: socket.socket, obj):
    payload = pickle.dumps(obj)
    sock.sendall(struct.pack("!I", len(payload)) + payload)

def recv_server_packet(sock: socket.socket):
    raw_len = recv_msg(sock, 4)
    if not raw_len:
        return None
    data_len = struct.unpack("!I", raw_len)[0]
    raw = recv_msg(sock, data_len)
    return pickle.loads(raw)