import socket
import time
import json

HOST = '127.0.0.1'
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))

    data = {"value": 42, "label": "ribeye"}
    json_str = json.dumps(data)
    s.sendall(json_str.encode())

    response_bytes = s.recv(1024)
    response_str = response_bytes.decode()
    response_obj = json.loads(response_str)

    print("Response:", response_obj)
    #for i in range(    20):
       # message = f"Ping {i + 1}"
        #s.sendall(message.encode())
        #data = s.recv(1024)
        #print(f"Server says: {data.decode()}")
        #time.sleep(1)  # wait for 1 second
    
    