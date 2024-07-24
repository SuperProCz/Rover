import pigpio
import time

pi = pigpio.pi()
duty_cycle = 0
while True:
    try:
        duty_cycle = int(input("Duty cycle in %: "))
        pi.hardware_PWM(18, 8000, int(1000000 * duty_cycle / 100))
        print(pi.get_PWM_frequency(18))

    except KeyboardInterrupt:
        print("keybor danejfnjskeGFIJ NASGH")
        pi.stop()
        break
        
        
