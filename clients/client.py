#client file

import socket

host = "127.0.0.1"
port = 9000

with socket.create_connection((host, port)) as s:
    s.sendall(b"hello\n")