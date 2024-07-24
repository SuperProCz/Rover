import socket
import threading
import os
from HoverSerial import *
import time

HOST = "10.42.0.1"
PORT = 1532

SERIAL_PORT = '/dev/ttyAMA4'
SERIAL_BAUD = 115200
hover_serial = Hoverboard_serial(SERIAL_PORT, SERIAL_BAUD)
connected = False
        
class USARTInterface:
    VALID_INPUT = ('steer', 'speed')
    SPEED_MAX, SPEED_MIDDLE, SPEED_MIN = (50, 0, -50)
    STEER_MAX, STEER_MIDDLE, STEER_MIN = (50, 0, -50)
    def __init__(self, steer: int, speed: int, board: Hoverboard_serial) -> None:
        self.board = board
        self.steer = steer
        self.speed = speed

    def setSpeed(self, newSpeed: int):
        self.speed = newSpeed
        self.update()
        
    def setSteer(self, newSteer: int):
        self.steer = newSteer
        self.update()

    def getSpeed(self):
        return self.speed
    
    def getSteer(self):
        return self.steer

    def setMinimumValue(self, value: str):
        if not value in self.VALID_INPUT:
            raise ValueError("Invalid value to change, only accepted values are: " + self.VALID_INPUT)
        if value == "steer":
            self.setSteer(self.STEER_MIN)
        elif value == "speed":
            self.setSpeed(self.SPEED_MIN)
        else:
            print("huh? this wasn't supposed to happen")
        #print("Value changed")
        self.update()

    def setMiddleValue(self, value: str):
        if not value in self.VALID_INPUT:
            raise ValueError("Invalid value to change, only accepted values are: " + self.VALID_INPUT)
        if value == "steer":
            self.setSteer(self.STEER_MIDDLE)
        elif value == "speed":
            self.setSpeed(self.SPEED_MIDDLE)
        else:
            print("huh? this wasn't supposed to happen")
        #print("Value changed")
        self.update()

    def setMaximumValue(self, value: str):
        if not value in self.VALID_INPUT:
            raise ValueError("Invalid value to change, only accepted values are: " + self.VALID_INPUT)
        if value == "steer":
            self.setSteer(self.STEER_MAX)
        elif value == "speed":
            self.setSpeed(self.SPEED_MAX)
        else:
            print("huh? this wasn't supposed to happen")
        #print("Value changed")
        self.update()

    
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
    while True:
        interface.update()
        time.sleep(TIME_SEND)

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
