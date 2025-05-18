from HoverSerial import *
import time

idk = Hoverboard_serial('/dev/ttyAMA4', 115200)
idk2 = Hoverboard_serial('/dev/ttyAMA2', 115200)
idk3 = Hoverboard_serial('/dev/ttyAMA3', 115200)

idks = [idk, idk2, idk3]
while True:
    for i in idks:
        i.send_command(0, 100)
        time.sleep(0.1)
    time.sleep(0.01)