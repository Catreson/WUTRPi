import RPi.GPIO as GPIO
from common import SHM
import time

ENGINE_MODE_CODES = {'A': 0, 'P': 1, 'L': 2}


def run_leds(offline=0):
    led_1 = 8000
    led_2 = 9000
    led_3 = 9500
    led_4 = 10000

    led_flash = 10450
    rev_limiter = 11000
    ptim = 0
    ecu_m = 'A'

    cm = SHM()
    cm.save('engine_mode', ENGINE_MODE_CODES[ecu_m])

    def ecu_ping(channel):
        nonlocal ptim, ecu_m
        tim = time.time()
        if ecu_m != 'L' and 0.3 > tim - ptim > 0.2:
            ecu_m = 'L'
            cm.save('engine_mode', ENGINE_MODE_CODES[ecu_m])
        elif tim - ptim > 2:
            ecu_m = 'P'
            cm.save('engine_mode', ENGINE_MODE_CODES[ecu_m])
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

    try:
        while True:
            tim = time.time()
            if ecu_m != 'A' and not GPIO.input(25) and tim - ptim > 1:
                ecu_m = 'A'
                cm.save('engine_mode', ENGINE_MODE_CODES[ecu_m])
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
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    run_leds()
