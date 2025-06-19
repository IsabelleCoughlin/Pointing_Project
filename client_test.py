import socket
import json
import time

HOST = '127.0.0.1'  # same IP as server
PORT = 65432        # same port as server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    for i in range(20):
        message = f"Ping {i + 1}"
        s.sendall(message.encode())
        data = s.recv(1024)
        print(f"Server says: {data.decode()}")
        time.sleep(1)  # wait for 1 second