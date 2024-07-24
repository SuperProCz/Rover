import socket
import threading
import os
from HoverSerial import *
import time

HOST = "10.42.0.1"
PORT = 1532

SERIAL_PORT = '/dev/ttyAMA4'
SERIAL_BAUD = 115200

GRADUAL_ACCELERATION = True

hover_serial = Hoverboard_serial(SERIAL_PORT, SERIAL_BAUD)
connected = False
        
class USARTInterface:
    VALID_INPUT = ('steer', 'speed')
    SPEED_MAX, SPEED_MIDDLE, SPEED_MIN = (1000, 0, -1000)
    STEER_MAX, STEER_MIDDLE, STEER_MIN = (1000, 0, -1000)
    def __init__(self, steer: int, speed: int, board: Hoverboard_serial) -> None:
        self.board = board
        self.steer = steer
        self.speed = speed
        self.targetSpeed = speed
        self.targetSteer = steer

    def setSpeed(self, newSpeed: int):
        self.speed = newSpeed
        self.update()
        
    def setSteer(self, newSteer: int):
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
        if not value in self.VALID_INPUT:
            raise ValueError("Invalid value to change, only accepted values are: " + self.VALID_INPUT)
        if value == "steer":
            self.setTargetSteer(self.STEER_MIN)
        elif value == "speed":
            self.setTargetSpeed(self.SPEED_MIN)
        else:
            print("huh? this wasn't supposed to happen")
        #print("Value changed")
        #self.update()

    def setMiddleValue(self, value: str):
        if not value in self.VALID_INPUT:
            raise ValueError("Invalid value to change, only accepted values are: " + self.VALID_INPUT)
        if value == "steer":
            self.setTargetSteer(self.STEER_MIDDLE)
        elif value == "speed":
            self.setTargetSpeed(self.SPEED_MIDDLE)
        else:
            print("huh? this wasn't supposed to happen")
        #print("Value changed")
        #self.update()

    def setMaximumValue(self, value: str):
        if not value in self.VALID_INPUT:
            raise ValueError("Invalid value to change, only accepted values are: " + self.VALID_INPUT)
        if value == "steer":
            self.setTargetSteer(self.STEER_MAX)
        elif value == "speed":
            self.setTargetSpeed(self.SPEED_MAX)
        else:
            print("huh? this wasn't supposed to happen")
        #print("Value changed")
        #self.update()

    
    def update(self):
        currentSpeed = self.getSpeed()
        currentSteer = self.getSteer()
        self.board.send_command(currentSteer, currentSpeed)
        #print('Sending:\t steer: '+str(currentSteer)+'speed: '+str(currentSpeed))

def usartFeedback(board: Hoverboard_serial):

    while True:

        feedback = board.receive_feedback()

        if feedback == None:
            continue
        
        #print('Receiving:\t', feedback)

def usartSending(interface: USARTInterface):
    TIME_SEND = 0.05 
    PERCENTAGE_STEP = 0.01
    wantedSpeed = 0
    wantedSteer = 0
    brokeOut = False
    while True:
        if GRADUAL_ACCELERATION:
            currentSpeed = interface.getSpeed()
            currentSteer = interface.getSteer()

            wantedSpeed = interface.getTargetSpeed()
            wantedSteer = interface.getTargetSteer()
            print(f"Current steer: {currentSteer}, wantedSteer: {wantedSteer}")
            print(f"Current speed: {currentSpeed}, wantedSpeed: {wantedSpeed}")
            #Don't touch those for loops, I don't know why it works, but it does.
            if currentSpeed < wantedSpeed:
                for i in range(1, int(100 / (PERCENTAGE_STEP * 100)) + 1, 1):
                    newSpeed = round(currentSpeed - ((currentSpeed-wantedSpeed) * i)* PERCENTAGE_STEP)
                    interface.setSpeed(newSpeed)
                    #print(f"Increasing speed: {newSpeed}, wanted speed: {wantedSpeed}")
                    time.sleep(TIME_SEND)
                    if interface.getTargetSpeed() != wantedSpeed:
                        brokeOut = True
                        break
#                1000            0
            elif currentSpeed > wantedSpeed:
                for i in range(1, int(100 / (PERCENTAGE_STEP * 100)) + 1, 1):
                    newSpeed = round(currentSpeed + ((wantedSpeed-currentSpeed) * PERCENTAGE_STEP) * i)
                    interface.setSpeed(newSpeed)
                    #print(f"Decreasing speed: {newSpeed}, wanted speed: {wantedSpeed}")
                    time.sleep(TIME_SEND)
                    if interface.getTargetSpeed() != wantedSpeed:
                        brokeOut = True
                        break

            if currentSteer < wantedSteer:
                for i in range(1, int(100 / (PERCENTAGE_STEP * 100)) + 1, 1):
                    newSteer = round(currentSteer - ((currentSteer-wantedSteer) * i)* PERCENTAGE_STEP)
                    interface.setSteer(newSteer)
                    print(f"Increasing steer: {newSteer}, wanted speed: {wantedSteer}")
                    time.sleep(TIME_SEND)  
                    if interface.getTargetSteer() != wantedSteer:
                        brokeOut = True
                        break

            elif currentSteer > wantedSteer:
                for i in range(1, int(100 / (PERCENTAGE_STEP * 100)) + 1, 1):
                    newSteer = round(currentSteer + ((wantedSteer-currentSteer) * PERCENTAGE_STEP) * i)
                    interface.setSteer(newSteer)
                    print(f"Decreasing steer: {newSteer}, wanted speed: {wantedSteer}")
                    time.sleep(TIME_SEND)
                    if interface.getTargetSteer() != wantedSteer:
                        brokeOut = True
                        break

            wantedSpeed = interface.getTargetSpeed()
            wantedSteer = interface.getTargetSteer()

        if not brokeOut:
            print("UPDATED")
            interface.update()
        time.sleep(TIME_SEND)
        brokeOut = False

motors1 = USARTInterface(0, 0, hover_serial)

def listen(conn, addr):
    global connected
    with conn:
        while True:
            data = conn.recv(1024)
            if len(data) == 0:
                print(f"Disconnected {addr}")
                connected = False
                return
            decodedData = data.decode().split(" ")
            print(f"Got: {decodedData[0]} and {decodedData[1]}")
            if decodedData[0] == "1":
                motors1.setMaximumValue("speed")
            elif decodedData[0] == "-1":
                motors1.setMinimumValue("speed")
            else:
                motors1.setMiddleValue("speed")

            if decodedData[1] == "1":
                motors1.setMaximumValue("steer")
            elif decodedData[1] == "-1":
                motors1.setMinimumValue("steer")
            else:
                motors1.setMiddleValue("steer")
        print("umm what?")
    print('hi mf')       

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    usartListenerThread = threading.Thread(target=usartFeedback, args=(hover_serial,))
    usartListenerThread.start()
    usartSendingThread = threading.Thread(target=usartSending, args=(motors1,))
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
            print("this fucking thread")
            with conn:
                print(f"Connected by {addr}")
                connected = True
                while connected:
                    if not listenThread.is_alive(): 
                        print("Listen thread ded")
                        continue
            print('closed conn')
        except KeyboardInterrupt:
            print("keyboard interrupted, stopping program")
            break
    print("hey yu mf")
