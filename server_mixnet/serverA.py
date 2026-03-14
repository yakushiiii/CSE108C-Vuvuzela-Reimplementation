from config import Rounds
import socket as sock
import time
import threading
import signal, sys
import queue
import asyncio
import hashlib
import json

import time
from config import BATCHING
from shuffle import shuffle

round_number = 1

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

def handle_client(conn, addr):
    client_messages = {}
    print(f"Client connected: {addr}")

    conn.settimeout(0.5)

    try:
        while True:
            try: 
                response = conn.recv(4096)
                if not response:
                    break
                with clients_lock:
                    client_messages[conn] = response
            except sock.timeout:
                print(f"Client timeout")
                continue
    finally:
        with clients_lock:
            client_messages.pop(conn, None)
        conn.close()
        print(f"Client disconnected: {addr}")
            
def batching(BATCHING, client_messages):

    batching_message = {
        "round_number": round_number,
        "message": "BATCHING_START"
    }

    batching_string = json.dumps(batching_message)
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
                broadcast(b"BATCHING_END")
            for x in client_messages:
                client_messages[x] = None
            
        if not batch_list:
            continue

        return batch_list
    
def return_message(conn_list, batch_list, round_number):
    for x in range(len(batch_list)):
        try:
            for conn in conn_list:
                conn.sendall(batch_list)
        except:
            print("Message has no swapped one??")
    print(f"Round {round_number} complete.  Incrementing")
    round_number += 1


def start_server(host="127.0.0.1", port=9000):
    with sock.sock(sock.AF_INET, sock.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print("Server listening")

        while True:
            conn, addr = s.accept()
            threading.Thread(
                target=handle_client,
                args=(conn, addr),
                daemon=True
            ).start()

async def init_rounds():
    rounds = Rounds()
    asyncio.create_task(server_A(rounds))
    await asyncio.Event().wait()
