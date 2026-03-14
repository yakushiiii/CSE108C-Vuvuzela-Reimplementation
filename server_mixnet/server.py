# Server Class Node

import socket, sleep, threading
from encryption import server_decrypt
from keys import keys

clients = set()
clients_lock = threading.Lock()

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

    def __init__(self, node_id, prev_node=None, next_node=None, session_key=None):
        self.id = node_id
        self.port = self.PORT_START + node_id
        self.prev_node = prev_node
        self.next_node = next_node
        self.private_key = keys[node_id][0]
        print("Done initializing Nodes")

    def handle_client(self, conn: socket.socket, addr):
        try:
            client_messages = []
            received_data = b""

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
                except socket.timeout:
                    print("socket timed out")
                    break
                finally:
                    with clients_lock:
                        client_messages.pop(conn, None)
                    conn.close()
                    print(f"Client disconnected: {addr}")

            if not received_data:
                return
            
            client_messages = {}
            print(f"Client connected: {addr}")

            conn.settimeout(0.5)


            decrypted_data = server_decrypt(self.private_key, received_data)
            header, payload = decrypted_data.split(b"|", 1)
            host, port = header.decode().split(":")
            port = int(port)

            # If there is a next node, forward encrypted data
            if self.next_node:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((host, port))
                    print("connected to next node")
                    s.sendall(payload)
                    print("Data Forwarded")
                    
                    response = b""
                    while True:
                        r = s.recv(4096)
                        if not r:
                            print("No response")
                            break
                        response += r
                        print("response received")
                encrypted_response = encrypt_message(response, self.private_key)
                conn.sendall(encrypted_response)
            else:
                # Last node: send HTTP request
                context = ssl.create_default_context()

                with socket.create_connection((host, port)) as sock:
                    with context.wrap_socket(sock, server_hostname=host) as ssock:
                        ssock.sendall(payload)
                        print("Final node sent")
                        response = b""
                        while True:
                            r = ssock.recv(4096)
                            if not r:
                                print("No response from HTTP")
                                break
                            response += r
                            print("response received from HTTP")

                encrypted_response = encrypt_message(response, self.private_key)
                conn.sendall(encrypted_response)

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
                t = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                t.start()