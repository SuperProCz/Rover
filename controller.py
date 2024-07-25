import sys, time
running = True
from pynput.keyboard import Key, Listener, KeyCode

#nice comment, I hope that I don't break anything by adding it here
xVel = 0
yVel = 0
alreadyPressed = {'w': False, 's': False, 'a': False, 'd': False}
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

def on_press(key):
    global xVel, yVel
    if type(key) == KeyCode:
        if key.char == 'w' and not alreadyPressed['w']:
            alreadyPressed['w'] = True
            changeVel('x', 1)
        elif key.char == 's' and not alreadyPressed['s']:
            alreadyPressed['s'] = True
            changeVel('x', -1)
        elif key.char == 'a' and not alreadyPressed['a']:
            alreadyPressed['a'] = True
            changeVel('y', -1)
        elif key.char == 'd' and not alreadyPressed['d']:
            alreadyPressed['d'] = True
            changeVel('y', 1)
        elif key.char == 'p':
            sendCommand(2)
    elif type(key) == Key:
        if key == Key.space:
            sendCommand(1)
    else:
        print("Unknown key pressed!!")
    
def on_release(key):
    global xVel, yVel
    if type(key) == KeyCode:
        if key.char == 'w':
            alreadyPressed['w'] = False
            changeVel('x', -1)
        elif key.char == 's':
            alreadyPressed['s'] = False
            changeVel('x', 1)
        elif key.char == 'a':
            alreadyPressed['a'] = False
            changeVel('y', 1)
        elif key.char == 'd':
            alreadyPressed['d'] = False
            changeVel('y', -1)
    elif type(key) == Key:
        pass

    else:
        pass
# Collect events until released

def main():
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

def changeConn(newConn):
    global conn
    conn = newConn
