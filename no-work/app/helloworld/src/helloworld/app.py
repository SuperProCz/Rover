"""
My first application
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
import toga.android
import socket

xVel = 0
yVel = 0
alreadyPressed = {'w': False, 's': False, 'a': False, 'd': False}
speedChange = {
    '1': 100,
    '2': 200,
    '3': 300,
    '4': 400,
    '5': 500,
    '6': 600,
    '7': 700,
    '8': 800,
    '9': 900,
    '0': 1000
}
conn = None

def changeVel(axis, value):
    global xVel, yVel
    if axis == 'x':
        xVel += value
    elif axis == 'y':
        yVel += value
    if conn != None or conn != "XXX":
        #print("sent!")
        sendCommand(0, xVel, yVel)
    else:
        return

    #print(f"xVel: {xVel}, yVel: {yVel}")

def sendCommand(id, *args):
    convertedValues = [str(value) for value in args]
    command = str(id) + " " + ' '.join(convertedValues) 
    conn.sendall(command.encode())
    print(f"sent: {command}")

# def on_press(key):
#     global xVel, yVel
#     if type(key) == KeyCode:
#         if key.char == 'w' and not alreadyPressed['w']:
#             alreadyPressed['w'] = True
#             changeVel('x', 1)
#         elif key.char == 's' and not alreadyPressed['s']:
#             alreadyPressed['s'] = True
#             changeVel('x', -1)
#         elif key.char == 'a' and not alreadyPressed['a']:
#             alreadyPressed['a'] = True
#             changeVel('y', -1)
#         elif key.char == 'd' and not alreadyPressed['d']:
#             alreadyPressed['d'] = True
#             changeVel('y', 1)
#         elif key.char == 'p':
#             sendCommand(2)
#         elif key.char in speedChange:
#             sendCommand(3, speedChange[key.char])
            
#     elif type(key) == Key:
#         if key == Key.space:
#             sendCommand(1)
#     else:
#         print("Unknown key pressed!!")
    
# def on_release(key):
#     global xVel, yVel
#     if type(key) == KeyCode:
#         if key.char == 'w':
#             alreadyPressed['w'] = False
#             changeVel('x', -1)
#         elif key.char == 's':
#             alreadyPressed['s'] = False
#             changeVel('x', 1)
#         elif key.char == 'a':
#             alreadyPressed['a'] = False
#             changeVel('y', 1)
#         elif key.char == 'd':
#             alreadyPressed['d'] = False
#             changeVel('y', -1)
#     elif type(key) == Key:
#         pass

#     else:
#         pass

class HelloWorld(toga.App):
    

    def startup(self):
        """Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """
        main_box = toga.Box(style=Pack(alignment=CENTER, direction=COLUMN))

        labelBox = toga.Box(style=Pack(direction=ROW, alignment=CENTER))
        myBox = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER))
        btns = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER))

        middleBtns = toga.Box(style=Pack(direction=ROW))
        label = toga.Label(
            "Test app!",
            style=Pack(flex=1, text_align=CENTER)
        )

        def button_handler(button):
            print(button.text)

        buttonUp = toga.Button(
            "Up",
            on_press=button_handler,
            #on_release=button_handler
        )

        buttonRight = toga.Button(
            "Right",
            on_press=button_handler,
        )

        buttonLeft = toga.Button(
            "Left",
            on_press=button_handler,
        )

        buttonDown = toga.Button(
            "Down",
            on_press=button_handler,
        )

        labelBox.add(label)

        middleBtns.add(buttonLeft, buttonRight)
        btns.add(buttonUp, middleBtns, buttonDown)
        myBox.add(labelBox, btns)
        main_box.add(myBox)
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()


def main():
    return HelloWorld()
