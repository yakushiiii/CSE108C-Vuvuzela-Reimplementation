#!/usr/bin/env python3
# main.py  –  Start all three mix-net nodes

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import threading
import socket


from server_mixnet import server
from config import BATCHING, NUMBER_NODES, SERVER_PORT, SERVER_IP_ADDRESS


# Build node chain:  node0 <-> node1 <-> node2

nodes = [server.Node(i) for i in range(NUMBER_NODES)]
for i, node in enumerate(nodes):
    node.prev_node = nodes[i - 1] if i > 0              else None
    node.next_node = nodes[i + 1] if i < len(nodes) - 1 else None

# Start each node's listener in a background thread

for node in nodes:
    threading.Thread(target=node.start, daemon=True).start()

# Start node 0's batching loop in a background thread

threading.Thread(target=nodes[0].batching, args=(BATCHING,), daemon=True).start()

# Front-door listener on SERVER_PORT
# Clients connect here; we forward to node 0's handle_client

print(f"Front door listening on {SERVER_IP_ADDRESS}: {SERVER_PORT}") #CHANGE
front = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
front.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
front.bind((SERVER_IP_ADDRESS, SERVER_PORT)) #so listens on all interfaces CHANGE
front.listen()

while True:
    conn, addr = front.accept()
    print(f"SERVER: accepted connection from {addr}")
    threading.Thread(
        target=nodes[0].handle_client, args=(conn, addr), daemon=True
    ).start()
