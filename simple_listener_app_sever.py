import socket
import threading
import os
from HoverSerial import *
import time
import multiprocessing
import configparser
import struct
import cv2 as cv
from cv2 import VideoCapture
from server_statuses import SERVER_STATUSES
from socket_headers import HEADERS

HOSTNAME = socket.gethostname()
#HOST = socket.gethostbyname(HOSTNAME)
HOST = '0.0.0.0'
PORT = 1532

SPEED_VALUES = (1000,0,-1000)
STEER_VALUES = (1000,0,-1000)

print(HOST)
print(HOSTNAME)

connected = False
showFeedback = False
canSendImg = False

imgSize = 0

maxDataSize = 2000

cam = VideoCapture(1)

def listen_old(conn, addr):
    global connected, showFeedback, SPEED_VALUES, STEER_VALUES
    with conn:
        while True:
            try:

                dataLength = int.from_bytes(conn.recv(2), byteorder='big')
                data = conn.recv(dataLength).decode('UTF-8')
                if data == 'nice':
                    print(data)
                if conn == None:
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
                    
                    imageSendingThread = threading.Thread(target=sendImage, args=(conn,))
                    imageSendingThread.start()

                #print(decodedData)
            except Exception:
                pass     

def commandHandler(data):
    pass

def checkImgSize(data):
        global imgSize, canSendImg
        if imgSize == int.from_bytes(data, byteorder='big'):
            canSendImg = True

def listen(conn, addr):
    global connected
    with conn:
        while True:
            try:
                header = conn.recv(8)

                packetType = header[0]
                dataSize = header[1:2]

                data = conn.recv(int.from_bytes(dataSize, byteorder='big'))

                if HEADERS["CMD"] == packetType:
                    commandHandler(data)
                elif HEADERS["STATUS"] == packetType:
                    pass
                elif HEADERS["IMG_SIZE"] == packetType:
                    checkImgSize(data=data)
            except Exception:
                print("Something went wrong while listening to incoming data")
def sendImage(conn):
    global imgSize
    while True:
        result, image = cam.read()
        if result:
            image_bytes = cv.imencode('.jpg', image)[1].tobytes()
            imgSize = len(image_bytes)
            data = HEADERS["IMG_SIZE"] + (32).to_bytes(4, byteorder='big') + (5 * b'\x00') + imgSize.to_bytes(4, byteorder='big')
            conn.sendall(data)
            #print("sent")

            #print("Received: ", int.from_bytes(received, byteorder='big'))
            # print("Received: ", received)
            # print("Received normal: ", int.from_bytes(received, "big"))
            # print("Actual: ", imageSize.to_bytes(32, byteorder='big'))
            # print("actual normal: ", imageSize)
            #comparing the decoded integer values (java has one extra byte to represent un/signed values)
            while True:
                if canSendImg:
                    canSendImg = False
                    conn.sendall(image_bytes)
                    break
            

def main():
    global connected
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
                if connected:
                    conn.sendall(SERVER_STATUSES["DENIED"].to_bytes(1, byteorder="big"))
                    conn.close()
                else:
                    print("accepted")
                    conn.sendall(SERVER_STATUSES["ACCEPTED"].to_bytes(1, byteorder="big"))
                    listenThread = threading.Thread(target=listen, args=(conn, addr))
                    listenThread.start()
                    with conn:
                        print(f"Connected by {addr}")
                        connected = True
                        while connected:
                            if not listenThread.is_alive(): 
                                break
                    print('closed conn')
            except KeyboardInterrupt:
                print("keyboard interrupted, stopping program")
                break
        print("hey yu mf")

if __name__ == "__main__":
    main()