import socket
import json
import time

HOST = '127.0.0.1'  # localhost aka on my computer both ways
PORT = 65432        # choose a port > 1024 random!

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))  # bind server to address
    s.listen()  # wait for a connection
    print(f"Listening on {HOST}:{PORT}")
    conn, addr = s.accept()  # accept a connection
    with conn:
        print(f"Connected by {addr}")
        data_byte = conn.recv(1024)
        data_str = data_byte.decode()
        data_obj = json.loads(data_str)

        print(f"Received: {data_obj}")

        data_obj["value"] += 10

        response_str = json.dumps(data_obj)
        conn.sendall(response_str.encode())
        
        #count = 0
        #while count < 20:
            #data = conn.recv(1024) # Receive the data
            #if not data:
            #    break
            #print(f"Received: {data.decode()}")
            #response = f"ACK {count + 1}"
            #conn.sendall(response.encode())
            #count += 1
