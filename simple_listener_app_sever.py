import socket
import threading
import os
from HoverSerial import *
import time
import multiprocessing
import configparser
import struct

HOSTNAME = socket.gethostname()
HOST = socket.gethostbyname(HOSTNAME+".local")
PORT = 1532

SPEED_VALUES = (1000,0,-1000)
STEER_VALUES = (1000,0,-1000)

print(HOST)
print(HOSTNAME)

connected = False
showFeedback = False

def listen(conn, addr):
    global connected, showFeedback, SPEED_VALUES, STEER_VALUES
    with conn:
        while True:
            try:

                dataLength = int.from_bytes(conn.recv(2), byteorder='big')
                data = conn.recv(dataLength).decode('UTF-8')
                if data == 'nice':
                    print(data)
                if len(data) == 0:
                    print(f"Disconnected {addr}")
                    connected = False
                    return
                decodedData = data.split(" ")

                print(decodedData)
                cmdId = int(decodedData[0])

                
                if cmdId == 3:
                    newSpeed = int(decodedData[1])
                    newValues = (newSpeed, 0, -newSpeed)

                    STEER_VALUES = newValues
                    SPEED_VALUES = newValues
                    
                elif cmdId == 4:
                    #print((int(decodedData[1]) / 100) * SPEED_VALUES[0])
                    #print((int(decodedData[2]) / 100) * STEER_VALUES[0])
                    pass

                elif cmdId == 5:

                    with open("spotik.png", "rb") as f:
                        pic = f.read()

                    imageSize = len(pic)
                    conn.sendall(imageSize.to_bytes(32, byteorder='big'))
                    #print("sent")
                    received = conn.recv(2048)

                    #print("Received: ", int.from_bytes(received, byteorder='big'))
                    print("Received: ", received)
                    print("Actual: ", imageSize.to_bytes(32, byteorder='big'))
                    print("actual normal: ", imageSize)
                    if received == imageSize.to_bytes(32, byteorder='big'):
                        print("<<<<<<<>>>???????")
                        conn.sendall(pic)
                        print("sent")
                    else:
                        conn.sendall(bytes([0]))
                #print(decodedData)
            except Exception:
                pass     
            
def main():
    with open("spotik.png", "rb") as f:
        pic = f.read()

    print(pic[:100])
    print(type(pic))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        print("haha")
        while True:
            try:
                print("bubu")
                s.listen()
                conn, addr = s.accept()
                print("accepted")
                listenThread = threading.Thread(target=listen, args=(conn, addr))
                listenThread.start()
                with conn:
                    print(f"Connected by {addr}")
                    connected = True
                    while connected:
                        if not listenThread.is_alive(): 
                            break
                        time.sleep(1)
                print('closed conn')
            except KeyboardInterrupt:
                print("keyboard interrupted, stopping program")
                break
        print("hey yu mf")

if __name__ == "__main__":
    main()