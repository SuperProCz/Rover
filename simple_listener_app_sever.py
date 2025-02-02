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

import platform
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

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

maxDataSize = 65536

imgDecoded = True

appsink = 0
#cam = VideoCapture(0)
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

def commandHandler(data, conn):
    #print("command got!")
    cmdId = data[0]

    if cmdId == 5:
        imageSendingThread = threading.Thread(target=sendImage, args=(conn,))
        imageSendingThread.start()

def checkImgSize(data):
        #print("got imgsize!")
        global imgSize, canSendImg
        if imgSize == int.from_bytes(data, byteorder='big'):
            canSendImg = True

def listen(conn, addr):
    global connected, imgDecoded
    with conn:
        while True:
            try:
                header = conn.recv(8)
                if len(header) == 0:
                    print(f"Disconnected {addr}")
                    connected = False
                    return
                packetType = header[0]
                dataSize = header[1:3]
                #print(header)
                #print(dataSize)
                #print(int.from_bytes(packetType, byteorder='big'))

                if dataSize != 0:
                    data = conn.recv(int.from_bytes(dataSize, byteorder='big'))
                
                #print(HEADERS["CMD"])
                #print(packetType)
                if HEADERS["CMD"] == packetType:
                    commandHandler(data, conn)
                elif HEADERS["STATUS"] == packetType:
                    pass
                elif HEADERS["IMG_SIZE"] == packetType:
                    checkImgSize(data=data)
                elif HEADERS["IMG_DECODED"] == packetType:
                    imgDecoded = True
            except Exception:
                print("Something went wrong while listening to incoming data")

def sendImage(conn):
    global imgSize, canSendImg, imgDecoded
    while True:
        if imgDecoded:
            imgDecoded = False
            #result, image = cam.read()
            sample = appsink.emit('pull-sample')
            if result:
                encode_param = [int(cv.IMWRITE_JPEG_QUALITY), 30]
                resized_image = cv.resize(image, (320, 240))
                result, image = cv.imencode('.jpg', resized_image, encode_param)
                if result:
                    image_bytes = image.tobytes()
                    imgSize = len(image_bytes)
                    data = HEADERS["IMG_SIZE"].to_bytes(1, byteorder='big') + (4).to_bytes(2, byteorder='big') + (5 * b'\x00') + imgSize.to_bytes(4, byteorder='big')
                    #print("sending img size!!")
                    conn.sendall(data)
                    #print(imgSize)

                    #print("Received: ", int.from_bytes(received, byteorder='big'))
                    # print("Received: ", received)
                    # print("Received normal: ", int.from_bytes(received, "big"))
                    # print("Actual: ", imageSize.to_bytes(32, byteorder='big'))
                    # print("actual normal: ", imageSize)
                    #comparing the decoded integer values (java has one extra byte to represent un/signed values)
                    while True:
                        if canSendImg:
                            #print("sending img!!")
                            canSendImg = False
                            imgBytesSent = 0
                            while True:
                                packetSize = min(maxDataSize, imgSize - imgBytesSent)
                                data = HEADERS["IMG"].to_bytes(1, byteorder='big') + (packetSize).to_bytes(2, byteorder='big') + (5 * b'\x00') + image_bytes[imgBytesSent:(imgBytesSent+packetSize)]
                                conn.sendall(data)
                                #TEMPCOUNTER += 1
                                imgBytesSent += packetSize
                                #print(packetSize)
                                #print(imgBytesSent)
                                if imgBytesSent == imgSize:
                                    imgSize = 0
                                    break
                            #print(TEMPCOUNTER)
                            #TEMPCOUNTER = 0
                            break
            
def create_pipeline():
    system = platform.system()

    if system == 'Darwin':  # mac
        pipeline = Gst.parse_launch(
            "v4l2src device=/dev/video0 ! video/x-raw,width=640,height=480,framerate=20/1 ! "
            "videoconvert ! vtenc_h264 ! video/x-h264,profile=baseline ! appsink name=sink"
        )
    elif system == 'Linux':  # RPi
        pipeline = Gst.parse_launch(
            "v4l2src device=/dev/video0 ! video/x-raw,width=640,height=480,framerate=20/1 ! "
            "videoconvert ! v4l2h264enc extra-controls=\"video_bitrate=500000\" ! "
            "video/x-h264,profile=baseline ! appsink name=sink"
        )
    else:
        raise Exception("Unsupported platform")

    return pipeline

def main():
    global connected

    pipeline = create_pipeline()

    # Get appsink element
    appsink = pipeline.get_by_name("sink")
    appsink.set_property("emit-signals", True)

    # Start pipeline
    pipeline.set_state(Gst.State.PLAYING)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        #s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
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
                s.close()
                break
        print("hey yu mf")

if __name__ == "__main__":
    main()