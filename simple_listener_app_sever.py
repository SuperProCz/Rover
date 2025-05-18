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

maxDataSize = 16384

imgDecoded = True

appsink = None

pipeline = None

cameraChanging = False
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

    print(cmdId)
    print(data)
    if cmdId == 5:
        print("starting img sending thread!")
        imageSendingThread = threading.Thread(target=sendImage, args=(conn,))
        imageSendingThread.start()
    elif cmdId == 6:
        print(data[1])
        changeCam(data[1])


def changeCam(id):
    global pipeline, cameraChanging
    if pipeline != None:
        cameraChanging = True
        print("Stopping current pipeline...")
        pipeline.set_state(Gst.State.NULL)
        pipeline = None

        print(f"Creating new pipeline for camera id: {id}")
        try:
            pipeline = create_pipeline(id)
        except Exception as e:
            print(f"Failed to create new pipeline: {e}")
            cameraChanging = False
            return

        # Retrieve and configure appsink
        appsink = pipeline.get_by_name("sink")
        if not appsink:
            print("Appsink not found in pipeline!")
            cameraChanging = False
            return
        #pipeline = create_pipeline(id)

        appsink = pipeline.get_by_name("sink")
        appsink.set_property("emit-signals", True)
        appsink.set_property("sync", False)  # Disable synchronization to reduce latency
        appsink.set_property("max-buffers", 1)  # Keep only the latest frame
        appsink.set_property("drop", True)
        appsink.set_property("max-lateness", 0)  # Make sure no buffer overrun

        print("Starting new pipeline...")
        pipeline.set_state(Gst.State.PLAYING)
        cameraChanging = False
    else:
        print("PIPELINE IS NONE WHILE CHANGING CAM")


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
        if imgDecoded and not cameraChanging:
            imgDecoded = False
            #result, image = cam.read()
            #encode_param = [int(cv.IMWRITE_JPEG_QUALITY), 30]
            #resized_image = cv.resize(image, (320, 240))
            #result, image = cv.imencode('.jpg', resized_image, encode_param)
            #image_bytes = image.tobytes()
            sample = appsink.emit('pull-sample')
            if not sample:
                # No sample available; wait a bit and try again.
                time.sleep(0.005)
                print("Fuck")
                continue
            try:
                buffer = sample.get_buffer()
                imgBytes = buffer.extract_dup(0, buffer.get_size())
            except Exception as e:
                print(f"Error extracting buffer: {e}")
                continue
            imgSize = len(imgBytes)
            imgSizePacket = HEADERS["IMG_SIZE"].to_bytes(1, byteorder='big') + (4).to_bytes(2, byteorder='big') + (5 * b'\x00') + imgSize.to_bytes(4, byteorder='big')
            #print("sending img size!!")
            conn.sendall(imgSizePacket)
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
                        data = HEADERS["IMG"].to_bytes(1, byteorder='big') + (packetSize).to_bytes(2, byteorder='big') + (5 * b'\x00') + imgBytes[imgBytesSent:(imgBytesSent+packetSize)]
                        conn.sendall(data)
                        #TEMPCOUNTER += 1
                        imgBytesSent += packetSize
                        #print(packetSize)
                        #print(imgBytesSent)
                        if imgBytesSent == imgSize:
                            imgSize = 0
                            #print("sent")
                            break
                        time.sleep(0.001)
                    #print(TEMPCOUNTER)
                    #TEMPCOUNTER = 0
                    break
                time.sleep(0.001)
        time.sleep(0.001)
            
def create_pipeline(id):
    system = platform.system()

    if system == 'Darwin':  # mac
        pipeline = Gst.parse_launch(
            f"avfvideosrc device-index={id} do-timestamp=true ! "
            "video/x-raw,width=640,height=480,framerate=30/1 ! "
            "videoconvert ! "
            "vtenc_h264 bitrate=3000 realtime=true max-keyframe-interval=1 allow-frame-reordering=false ! "
            "h264parse config-interval=1 ! "
            "video/x-h264,stream-format=byte-stream,profile=baseline ! "
            "appsink name=sink max-buffers=1 drop=true sync=true"
        )
    elif system == 'Linux':  # RPi
        pipeline = Gst.parse_launch(
            "filesrc location=output.mp4 ! "
            "qtdemux ! queue ! "
            "decodebin ! videoconvert ! "
#            "v4l2h264enc extra-controls=\"cid,video_bitrate=5000\"  min-force-key-unit-interval=1000000000 ! "
            "v4l2h264enc extra-controls=cid,video_gop_size=2,video_bitrate_mode=1,video_bitrate=850_000 !"
            "h264parse config-interval=1 ! "
            "video/x-h264,stream-format=byte-stream,profile=baseline,level=(string)4 ! "
            "appsink name=sink max-buffers=1 drop=false sync=false"
        )
    else:
        raise Exception("Unsupported platform")

    return pipeline

def main():
    global connected, appsink, pipeline 
    Gst.init(None)
    pipeline = create_pipeline(0)

    # Get appsink element
    appsink = pipeline.get_by_name("sink")
    appsink.set_property("emit-signals", True)

    appsink.set_property("sync", False)  # Disable synchronization to reduce latency
    appsink.set_property("max-buffers", 1)  # Keep only the latest frame
    appsink.set_property("drop", True)
    appsink.set_property("max-lateness", 0)  # Make sure no buffer overrun
    # Start pipeline
    pipeline.set_state(Gst.State.PLAYING)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
                            time.sleep(0.001)
                    print('closed conn')
            except KeyboardInterrupt:
                print("keyboard interrupted, stopping program")
                s.close()
                break
        print("hey yu mf")

if __name__ == "__main__":
    main()