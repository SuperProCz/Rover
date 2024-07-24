import socket
import threading
import controller

HOST = "10.42.0.1"  
PORT = 1532 

controllerThread = threading.Thread(target=controller.main)
controllerThread.start()

def listen(socket):
    while True:
        data = socket.recv(1024)
        if len(data) == 0:
            print("Server disconnected (press Enter to continue)")
            return
        print("")
        print(f"Got: {data.decode()}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    controller.changeConn(s)
    listenThread = threading.Thread(target=listen, args=(s,))
    listenThread.start()
    
    while True:
        try:
            if not listenThread.is_alive():
                break
            #x = input("Send: ")
            #s.sendall(x.encode())
        except KeyboardInterrupt:
            print("Keyboard interrupted, breaking!")
            break
