import RPi.GPIO as GPIO
from common import SHM
import time

led_1 = 10100
led_2 = 10200
led_3 = 10300
led_4 = 10400
led_flash = 10450
rev_limiter = 11000

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(23, GPIO.OUT) # gear_set
GPIO.setup(24, GPIO.OUT) # gear_reset
GPIO.setup(21, GPIO.OUT) # led1
GPIO.setup(20, GPIO.OUT) # led2
GPIO.setup(16, GPIO.OUT) # led3
GPIO.setup(12, GPIO.OUT) # led 4

def display_gear(current_gear):
    GPIO.output(23, GPIO.HIGH)
    GPIO.output(23, GPIO.LOW)
    for i in range(current_gear):
        GPIO.output(24, GPIO.HIGH)
        GPIO.output(24, GPIO.LOW)

flash = 0
prev_gear = 0.0
cm = SHM()

while 1:
    rpm = cm.read("rpm")
    gear = cm.read("gear")
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
    elif rpm > rev_limiter:
        GPIO.output(21, GPIO.LOW)
        GPIO.output(20, GPIO.LOW)
        GPIO.output(16, GPIO.LOW)
        GPIO.output(12, GPIO.LOW)
    time.sleep(0.1)
