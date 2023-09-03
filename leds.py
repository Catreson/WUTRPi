import RPi.GPIO as GPIO
from common import SHM
import time

led_1 = 10100
led_2 = 10200
led_3 = 10300
led_4 = 10400
led_flash = 10450

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(21, GPIO.OUT) # led1
GPIO.setup(20, GPIO.OUT) # led2
GPIO.setup(16, GPIO.OUT) # led3
GPIO.setup(12, GPIO.OUT) # led 4

flash = 0

cm = SHM()

while 1:
    rpm = cm.read("rpm")
    if led_1 > rpm:
        GPIO.output(21, GPIO.LOW)
        GPIO.output(20, GPIO.LOW)
        GPIO.output(16, GPIO.LOW)
        GPIO.output(12, GPIO.LOW)
    elif led_2 > rpm:
        GPIO.output(21, GPIO.HIGH)
        GPIO.output(20, GPIO.LOW)
        GPIO.output(16, GPIO.LOW)
        GPIO.output(12, GPIO.LOW)
    elif led_3 > rpm:
        GPIO.output(21, GPIO.HIGH)
        GPIO.output(20, GPIO.HIGH)
        GPIO.output(16, GPIO.LOW)
        GPIO.output(12, GPIO.LOW)
    elif led_4 > rpm:
        GPIO.output(21, GPIO.HIGH)
        GPIO.output(20, GPIO.HIGH)
        GPIO.output(16, GPIO.HIGH)
        GPIO.output(12, GPIO.LOW)
    elif led_flash > rpm:
        GPIO.output(21, GPIO.HIGH)
        GPIO.output(20, GPIO.HIGH)
        GPIO.output(16, GPIO.HIGH)
        GPIO.output(12, GPIO.HIGH)
    elif rpm > led_flash:
        if flash == 0:
            GPIO.output(21, GPIO.HIGH)
            GPIO.output(20, GPIO.HIGH)
            GPIO.output(16, GPIO.HIGH)
            GPIO.output(12, GPIO.HIGH)
            flash = 1
        else:
            GPIO.output(21, GPIO.LOW)
            GPIO.output(20, GPIO.LOW)
            GPIO.output(16, GPIO.LOW)
            GPIO.output(12, GPIO.LOW)
            flash = 0
    time.sleep(0.1)
