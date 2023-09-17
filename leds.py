import RPi.GPIO as GPIO
from common import SHM, MQTT_CLIENT
import time

led_1 = 10100
led_2 = 10200
led_3 = 10300
led_4 = 10400
led_flash = 10450
rev_limiter = 11000
ptim = 0
tim = 0
ecu_m = 'A'
topic = "bike/display/ecu"

print('MQTT init')
mqtit = MQTT_CLIENT(client_id='leds')

def ecu_ping(channel):
    global ptim
    global mqtit
    global ecu_m
    tim = time.time()
    if ecu_m != 'L' and 0.3 > tim - ptim > 0.2:
        ecu_m = 'L'
        mqtit.send(topic, "L")
    elif tim - ptim > 2:
        ecu_m = 'P'
        mqtit.send(topic, 'P')
    ptim = tim

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(23, GPIO.OUT) # gear_set
GPIO.setup(24, GPIO.OUT) # gear_reset
GPIO.setup(21, GPIO.OUT) # led1
GPIO.setup(20, GPIO.OUT) # led2
GPIO.setup(16, GPIO.OUT) # led3
GPIO.setup(12, GPIO.OUT) # led 4
GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # ecu
GPIO.add_event_detect(25, GPIO.RISING,
            callback=ecu_ping, bouncetime=100)

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
    tim = time.time()
    if ecu_m != 'A' and not GPIO.input(25) and tim - ptim > 2:
        ecu_m = 'A'
        mqtit.send(topic, "A")
    rpm = cm.read("rpm")
    gear = cm.read("gear")
    if GPIO.input(25) and ecu_m != 'L':
        ecu_m = 'P'
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
    elif rev_limiter > rpm:
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
