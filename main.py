#!/usr/bin/env python3
# main.py  –  Start all three mix-net nodes
#
# Usage:  python main.py
#
# Each node runs in its own thread.  Node 0 also runs the batching loop.
# Clients connect to 127.0.0.1:9000 (SERVER_PORT).
#
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import threading
import socket
import struct
import json


from server_mixnet import server
from config import BATCHING, NUMBER_NODES, SERVER_PORT


# ---------------------------------------------------------------------------
# Build node chain:  node0 <-> node1 <-> node2
# ---------------------------------------------------------------------------

nodes = [server.Node(i) for i in range(NUMBER_NODES)]
for i, node in enumerate(nodes):
    node.prev_node = nodes[i - 1] if i > 0              else None
    node.next_node = nodes[i + 1] if i < len(nodes) - 1 else None

# ---------------------------------------------------------------------------
# Start each node's listener in a background thread
# ---------------------------------------------------------------------------

for node in nodes:
    threading.Thread(target=node.start, daemon=True).start()

# ---------------------------------------------------------------------------
# Start node 0's batching loop in a background thread
# ---------------------------------------------------------------------------

threading.Thread(target=nodes[0].batching, args=(BATCHING,), daemon=True).start()

# ---------------------------------------------------------------------------
# Front-door listener on SERVER_PORT
# Clients connect here; we forward to node 0's handle_client
# ---------------------------------------------------------------------------

print(f"Front door listening on all 169.233.245.218:{SERVER_PORT}")
front = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
front.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
front.bind(("169.233.245.218", SERVER_PORT)) #so listens on all interfaces
front.listen()

while True:
    conn, addr = front.accept()
    print(f"SERVER: accepted connection from {addr}")
    threading.Thread(
        target=nodes[0].handle_client, args=(conn, addr), daemon=True
    ).start()
