import socket
import threading
import os
from HoverSerial import *
import time
import multiprocessing
import configparser
import struct
import logging

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

conn = 0

print(HOST)
print(HOSTNAME)
PERCENTAGE_STEP = 0.1

WANTED_SPEED = 0
WANTED_STEER = 0

CURRENT_SPEED = 0
CURRENT_STEER = 0


SPEED_VALUES = ()
STEER_VALUES = ()


logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
interfaces = []
connected = False
#showFeedback = False
estopped = False

canSendImg = False

imgSize = 0

maxDataSize = 16384

imgDecoded = True

appsink = None

pipeline = None

cameraChanging = False

def loadConfig():
    global config, interfaces
    global GRADUAL_ACCELERATION, PERCENTAGE_STEP, SPEED_VALUES, STEER_VALUES

    config.read('config.ini')

    GRADUAL_ACCELERATION = config.getboolean('Settings', 'gradualacceleration')
    PERCENTAGE_STEP = config.getfloat('Settings', 'percentagestep')

    
    if config.getboolean("Settings", 'unitedspeed'):
            speed = config.getint('Settings', 'speed')
            SPEED_VALUES = (speed, 0, -speed)
            STEER_VALUES = (speed, 0, -speed)
    else:    
        SPEED_VALUES = tuple(settings['SpeedValues'])
        STEER_VALUES = tuple(settings['SteerValues'])
            
    boards = config.items('Boards')
    for board in boards:
        print(board[1])
        settings = eval(board[1])
        SERIAL_PORT = settings['UartInterface']
        SERIAL_BAUD = int(settings['BaudRate'])
    
        hover_serial = Hoverboard_serial(SERIAL_PORT, SERIAL_BAUD)

        interface = USARTInterface(0, 0, hover_serial, SPEED_VALUES, STEER_VALUES)

        interfaces.append(interface)

    print(SPEED_VALUES)

def createConfig():
    global config
    config['Boards'] = {
        "DefaultBoard": {
            "UartInterface": "/dev/ttyAMA4",
            "BaudRate": 115200
        },
        "SecondTestBoard": {
            "UartInterface": "/dev/ttyAMA3",
            "BaudRate": 115200
        },
        "ThirdTestBoard": {
            "UartInterface": "/dev/ttyAMA2",
            "BaudRate": 115200
        }
    }
    config['Settings'] = {
        "GradualAcceleration": True,
        "PercentageStep": 0.1,
        "UnitedSpeed": False,
        "Speed": 1000,
        "SpeedValues": (1000, 0, -1000),
        "SteerValues": (1000, 0, -1000)
    }

    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def commandHandler(data, conn):
    global WANTED_SPEED, WANTED_STEER
    #print("command got!")
    cmdId = data[0]

    if cmdId == 5:
        print("starting img sending thread!")
        imageSendingThread = threading.Thread(target=sendImage, args=(conn,))
        imageSendingThread.start()
    elif cmdId == 6:
        print(f"Changing camId to: {data[1]}")
        changeCam(data[1])
    elif cmdId == 4:
        #print("FIRST THING: " + str(round(((data[1] - 1) / 100) * SPEED_VALUES[0])))
        #print("SECOND THING: " + str(round(((data[2] -1) / 100) * STEER_VALUES[0])))
        WANTED_SPEED = round(((data[2] - 100) / 100) * SPEED_VALUES[0])
        WANTED_STEER = round(((data[1] -100) / 100) * STEER_VALUES[0])


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

class USARTInterface:
    global WANTED_SPEED, WANTED_STEER, CURRENT_SPEED, CURRENT_STEER
    VALID_INPUT = ('steer', 'speed')
    #SPEED_MAX, SPEED_MIDDLE, SPEED_MIN = (1000, 0, -1000)
    #STEER_MAX, STEER_MIDDLE, STEER_MIN = (1000, 0, -1000)
    def __init__(self, steer: int, speed: int, board: Hoverboard_serial, speedValues, steerValues) -> None:
        self.board = board
        self.steer = steer
        self.speed = speed
        self.targetSpeed = speed
        self.targetSteer = steer
        self.speedValues = speedValues
        self.steerValues = steerValues
    
    def changeSpeedValues(self, newValues):
        self.speedValues = newValues

    def changeSteerValues(self, newValues):
        self.steerValues = newValues


    def getBoard(self):
        return self.board
    
    def setSpeed(self, newSpeed: int):
        global CURRENT_SPEED
        CURRENT_SPEED = newSpeed
        self.speed = newSpeed
        self.update()
        
    def setSteer(self, newSteer: int):
        global CURRENT_STEER
        CURRENT_STEER = newSteer
        self.steer = newSteer
        self.update()

    def setTargetSpeed(self, newSpeed: int):
        self.targetSpeed = newSpeed

    def setTargetSteer(self, newSteer: int):
        self.targetSteer = newSteer

    def getTargetSpeed(self):
        return self.targetSpeed

    def getTargetSteer(self):
        return self.targetSteer

    def getSpeed(self):
        return self.speed
    
    def getSteer(self):
        return self.steer

    def setMinimumValue(self, value: str):
        global WANTED_SPEED, WANTED_STEER
        if not value in self.VALID_INPUT:
            raise ValueError("Invalid value to change, only accepted values are: " + self.VALID_INPUT)
        if value == "steer":
            WANTED_STEER = self.steerValues[2]
        elif value == "speed":
            WANTED_SPEED = self.speedValues[2]
        else:
            print("huh? this wasn't supposed to happen")
        #print("Value changed")
        #self.update()

    def setMiddleValue(self, value: str):
        global WANTED_SPEED, WANTED_STEER
        if not value in self.VALID_INPUT:
            raise ValueError("Invalid value to change, only accepted values are: " + self.VALID_INPUT)
        if value == "steer":
            WANTED_STEER = self.steerValues[1]
        elif value == "speed":
            WANTED_SPEED = self.speedValues[1]
        else:
            print("huh? this wasn't supposed to happen")
        #print("Value changed")
        #self.update()

    def setMaximumValue(self, value: str):
        global WANTED_SPEED, WANTED_STEER
        if not value in self.VALID_INPUT:
            raise ValueError("Invalid value to change, only accepted values are: " + self.VALID_INPUT)
        if value == "steer":
            WANTED_STEER = self.steerValues[0]
        elif value == "speed":
            WANTED_SPEED = self.speedValues[0]
        else:
            print("huh? this wasn't supposed to happen")
        #print("Value changed")
        #self.update()

    
    def update(self):
        currentSpeed = CURRENT_SPEED
        currentSteer = CURRENT_STEER

        self.getBoard().send_command(currentSteer, currentSpeed)
        #print('Sending:\t steer: '+str(currentSteer)+'speed: '+str(currentSpeed))

def usartFeedback():
    while True:
        feedback = interfaces[0].getBoard().receive_feedback()

        if feedback == None:
            #print("Continuing")
            continue
        
        print("bububu")
        print('Feedback:\t', feedback)
        logger.boards(feedback)

        time.sleep(0.001)

def usartSending():
    TIME_SEND = 0.01 #otestovat 0.1, v config.h je timeout 0.8s
    wantedSpeed = 0
    wantedSteer = 0
    changeSpeed = 0
    changeSteer = 0

    while True:
        if estopped:
            print("ESTOP PRESSED!! CUTTING USART COMMUNICATION!!")
            for interface in interfaces:
                interface.setSpeed(0)
                interface.setSteer(0)
                time.sleep(0.01)
                #interface.update()
            break
        if GRADUAL_ACCELERATION:
            currentSpeed = CURRENT_SPEED
            currentSteer = CURRENT_STEER

            wantedSpeed = WANTED_SPEED
            wantedSteer = WANTED_STEER
            #print(f"Current steer: {currentSteer}, wantedSteer: {wantedSteer}")
            #print(f"Current speed: {currentSpeed}, wantedSpeed: {wantedSpeed}")
            #Don't touch those for loops, I don't know why it works, but it does.
#              0              1000
            if currentSpeed < wantedSpeed and changeSpeed <= 0:
                changeSpeed = -((currentSpeed-wantedSpeed))* PERCENTAGE_STEP

#                1000            0
            elif currentSpeed > wantedSpeed and changeSpeed >= 0:
                changeSpeed = ((wantedSpeed-currentSpeed) * PERCENTAGE_STEP)
                    
            elif currentSpeed == wantedSpeed:
                changeSpeed = 0

            if currentSteer < wantedSteer and changeSteer <= 0:
                changeSteer = -((currentSteer-wantedSteer))* PERCENTAGE_STEP


            elif currentSteer > wantedSteer and changeSteer >= 0:
                changeSteer = ((wantedSteer-currentSteer) * PERCENTAGE_STEP)

            elif currentSteer == wantedSteer:
                changeSteer = 0

            #why is this here twice?
            wantedSpeed = WANTED_SPEED
            wantedSteer = WANTED_STEER

            for interface in interfaces:
                interface.setSpeed(round(currentSpeed + changeSpeed))
                interface.setSteer(round(currentSteer + changeSteer))

                if abs(wantedSpeed - interface.getSpeed()) < 50:
                    interface.setSpeed(wantedSpeed)

                if abs(wantedSteer - interface.getSteer()) < 50:
                    interface.setSteer(wantedSteer)
        else:
            for interface in interfaces:
                interface.setSteer(WANTED_STEER)
                interface.setSpeed(WANTED_SPEED)
                time.sleep(0.01)
        #print("UPDATED")
        for interface in interfaces:
            interface.update()
            time.sleep(0.01)
        #print("MUHHAUHAUHAUHAUH")
        time.sleep(TIME_SEND)

def listen_old(conn, addr):
    global connected, showFeedback, estopped, SPEED_VALUES, STEER_VALUES, WANTED_SPEED, WANTED_STEER
    with conn:
        while True:
            dataLength = int.from_bytes(conn.recv(2), byteorder='big')
            data = conn.recv(dataLength).decode('UTF-8')
            if data == 'nice':
                print(data)
            if len(data) == 0:
                print(f"Disconnected {addr}")
                connected = False
                return
            decodedData = data.split(" ")

            #print(decodedData)
            cmdId = int(decodedData[0])
            #print(decodedData)
            if cmdId == 0:
                if decodedData[1] == "1":
                    for interface in interfaces:
                        interface.setMaximumValue("speed")
                elif decodedData[1] == "-1":
                    for interface in interfaces:
                        interface.setMinimumValue("speed")
                else:
                    for interface in interfaces:
                        interface.setMiddleValue("speed")

                if decodedData[2] == "1":
                    for interface in interfaces:
                        interface.setMaximumValue("steer")
                elif decodedData[2] == "-1":
                    for interface in interfaces:
                        interface.setMinimumValue("steer")
                else:
                    for interface in interfaces:
                        interface.setMiddleValue("steer")
            #show feedback from board(doesnt work)
            elif cmdId == 1:
                showFeedback = True
                print("Got!!")
                
            #trigger estop
            elif cmdId == 2:
                estopped = True
                
            #changing steer/speed values
            elif cmdId == 3:
                newSpeed = int(decodedData[1])
                newValues = (newSpeed, 0, -newSpeed)
                
                STEER_VALUES = newValues
                SPEED_VALUES = newValues
            #truning joystick values to wanted values
            elif cmdId == 4:
                #print(SPEED_VALUES)
                #print(STEER_VALUES)
                WANTED_SPEED = round((int(decodedData[1]) / 100) * SPEED_VALUES[0])
                WANTED_STEER = round((int(decodedData[2]) / 100) * STEER_VALUES[0])

            else:
                raise ValueError(f"Invalid cmdId {cmdId}!!")

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
            except Exception as e:
                print(e)
                return

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
            # Live USB camera instead of filesrc
            "v4l2src device=/dev/video0 do-timestamp=true ! "
            # match your 640×480@30 settings
            "video/x-raw,width=640,height=480,framerate=30/1 ! "
            "videoconvert ! "
            # same encoder + extra-controls exactly as before, but quoted
            "v4l2h264enc extra-controls=\"cid,video_gop_size=2,video_bitrate_mode=1,video_bitrate=1_750_000\" ! "
            "h264parse config-interval=1 ! "
            "video/x-h264,stream-format=byte-stream,profile=baseline,level=(string)4 ! "
            "appsink name=sink max-buffers=1 drop=false sync=false"
        )

    else:
        raise Exception("Unsupported platform")

    return pipeline

def addLoggingLevel(levelName, levelNum, methodName=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present 

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
       raise AttributeError('{} already defined in logging module'.format(levelName))
    if hasattr(logging, methodName):
       raise AttributeError('{} already defined in logging module'.format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
       raise AttributeError('{} already defined in logger class'.format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)
    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)

def main():
    global connected, appsink, pipeline

    FORMAT = '%(levelname)s %(asctime)s %(message)s'
    logging.basicConfig(filename='test.log', level=logging.INFO, format=FORMAT)
    addLoggingLevel('BOARDS', logging.DEBUG - 5)

    logger.info("Logging started.")
    if not os.path.isfile('config.ini'):
        createConfig()
        logger.info("Config file created.")
    
    loadConfig()

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
    
    logger.info("Gstreamer setup.")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        s.bind((HOST, PORT))
        logger.info("Server binded")
        usartSendingThread = threading.Thread(target=usartSending)
        usartSendingThread.start()
        logger.info("usartSending() started")
        while True:
            try:
                s.listen()
                conn, addr = s.accept()
                if connected:
                    conn.sendall(SERVER_STATUSES["DENIED"].to_bytes(1, byteorder="big"))
                    conn.close()
                    logger.warn("Client denied")
                else:
                    print("accepted")
                    conn.sendall(SERVER_STATUSES["ACCEPTED"].to_bytes(1, byteorder="big"))
                    listenThread = threading.Thread(target=listen, args=(conn, addr))
                    listenThread.start()
                    logger.info("Client accepted and listen thread started")
                    with conn:
                        print(f"Connected by {addr}")
                        usartListenerThread = multiprocessing.Process(target=usartFeedback)
                        usartListenerThread.start()
                        listenThread.info()
                        connected = True
                        while connected:
                            if not listenThread.is_alive(): 
                                break
                            time.sleep(0.001)
                    print('closed conn')
            except KeyboardInterrupt:
                print("keyboard interrupted, stopping program")
                break
        print("hey yu mf")

if __name__ == "__main__":
    main()
