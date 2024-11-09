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

print(HOST)
print(HOSTNAME)
PERCENTAGE_STEP = 0.1

WANTED_SPEED = 0
WANTED_STEER = 0

CURRENT_SPEED = 0
CURRENT_STEER = 0


SPEED_VALUES = ()
STEER_VALUES = ()

config = configparser.ConfigParser()
interfaces = []
connected = False
showFeedback = False
estopped = False
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
            "BaudRate": 115200,
            "SpeedValues": (1000, 0, -1000),
            "SteerValues": (1000, 0, -1000)
        },
        "SecondTestBoard": {
            "UartInterface": "/dev/ttyAMA3",
            "BaudRate": 115200,
            "SpeedValues": (1000, 0, -1000),
            "SteerValues": (1000, 0, -1000)
        },
        "ThirdTestBoard": {
            "UartInterface": "/dev/ttyAMA2",
            "BaudRate": 115200,
            "SpeedValues": (1000, 0, -1000),
            "SteerValues": (1000, 0, -1000)
        }
    }
    config['Settings'] = {
        "GradualAcceleration": True,
        "PercentageStep": 0.1,
        "UnitedSpeed": False,
        "Speed": 1000
    }

    with open('config.ini', 'w') as configfile:
        config.write(configfile)

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
    global showFeedback
    while True:
        for interface in interfaces:
            feedback = interface.getBoard().receive_feedback()

            if feedback == None:
                #print("Continuing")
                continue
                
            if showFeedback:
                print("bububu")
                showFeedback = False    
                print('Feedback:\t', feedback)

def usartSending():
    TIME_SEND = 0.01 
    wantedSpeed = 0
    wantedSteer = 0

    while True:
        if estopped:
            print("ESTOP PRESSED!! CUTTING USART COMMUNICATION!!")
            for interface in interfaces:
                interface.setSpeed(0)
                interface.setSteer(0)
                interface.update()
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
        #print("UPDATED")
        for interface in interfaces:
            interface.update()
        time.sleep(TIME_SEND)

def listen(conn, addr):
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
            elif cmdId == 1:
                showFeedback = True
                print("Got!!")

            elif cmdId == 2:
                estopped = True
            
            elif cmdId == 3:
                newSpeed = int(decodedData[1])
                newValues = (newSpeed, 0, -newSpeed)
                
                STEER_VALUES = newValues
                SPEED_VALUES = newValues

            elif cmdId == 4:
                #print(SPEED_VALUES)
                #print(STEER_VALUES)
                WANTED_SPEED = round((int(decodedData[1]) / 100) * SPEED_VALUES[0])
                WANTED_STEER = round((int(decodedData[2]) / 100) * STEER_VALUES[0])

            else:
                raise ValueError(f"Invalid cmdId {cmdId}!!")
            
def main():
    if not os.path.isfile('config.ini'):
        createConfig()
    
    loadConfig()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        usartListenerThread = multiprocessing.Process(target=usartFeedback)
        usartListenerThread.start()
        usartSendingThread = threading.Thread(target=usartSending)
        usartSendingThread.start()
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
                print('closed conn')
            except KeyboardInterrupt:
                print("keyboard interrupted, stopping program")
                break
        print("hey yu mf")

if __name__ == "__main__":
    main()