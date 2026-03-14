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

round_number = 1
DUMMY_MESSAGE = "this is a dummy message"

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

    inbox = queue.Queue()

    with clients_lock:
        clients.add((conn, inbox))
    print(f"Client connected: {addr}")

    conn.settimeout(0.5)

    try:
        while True:
            try: 
                response = conn.recv(4096)
                if not response:
                    break
                inbox.put(response)
            except sock.timeout:
                print(f"Client timeout")
                continue
    finally:
        with clients_lock:
            clients.discard((conn, inbox))
        conn.close()
        print(f"Client disconnected: {addr}")
            
def batching(BATCHING):

    batching_message = {
        "round_number": round_number,
        "message": "BATCHING_START"
    }

    batching_string = json.dumps(batching_message)
    batching_bytes = batching_string.encode()

    while True:
        broadcast(batching_bytes)
        time.sleep(BATCHING)
        message_list = []

        with clients_lock:
            for conn, inbox in clients:
                try:
                    msg = inbox.get_nowait()
                except queue.Empty:
                    print("Queue Empty")
                    msg = DUMMY_MESSAGE
                message_list.append(msg)

        broadcast(b"BATCHING_END")
        round_number += 1
        return message_list


def start_server(host="127.0.0.1", port=9000):
    with sock.sock(sock.AF_INET, sock.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print("Server listening")

        while True:
            conn, addr = s.accept()
            threading.Thread(
                target=batching,
                args=(conn, addr),
                daemon=True
            ).start()

async def init_rounds():
    rounds = Rounds()
    asyncio.create_task(server_A(rounds))
    await asyncio.Event().wait()


################################################################################

'''
def handle_connection(conn: socket.socket, addr):
    try:
        data = conn.recv(4096)
        #do something with this data
    finally: 
        conn.close()

def main(): 
    if len(sys.argv) < 2:
        print(f"wrong argumets: {sys.argv[0]} port_num", file=sys.stderr)
        print(f"usage: {sys.argv[0]} <port>", file=sys.stderr)
        return 1
    
    try:
        port = int(sys.argv[1], 10)
    except ValueError:
        sys.stderr.write("Invalid Port\n\")

if __name__ == "__main__":
    raise SystemExit(main())
'''