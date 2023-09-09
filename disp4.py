import pygame
import os
import time
from common import SHM, MQTT_CLIENT
import logging
import sys
import RPi.GPIO as GPIO

os.environ["DISPLAY"] = ":0"
pygame.init()

laptime = 0.0
delta = 0.0
lapno = 0

# display configuration -------------------
display_resolution = [800, 480]
inversion = -1
screen_mode = -1
rpm_max = 12000
rpm = 1350

# offsets
width1 = 800 / 4
height1 = 420 / 3
offtop = 100
off1 = 15
offtop0 = 25
off2 = 115
height2 = 480 / 3

# click counts
fc_count = 0
rc_count = 0
st_count = 0
pb_count = 0

# font setup
cfont0 = (240, 240, 240)
cfont1 = (0, 0, 0)
rpm_col = (200, 200, 200)
font1 = pygame.font.SysFont(None, 180)
font2 = pygame.font.SysFont(None, 100)

FPS = 10
fpsClock = pygame.time.Clock()
# end of display configuration -------------

# GPIO config
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# end GPIO config

screen = pygame.display.set_mode(display_resolution, pygame.FULLSCREEN)
# screen = pygame.display.set_mode(display_resolution)
pygame.display.set_caption('Display')
screen_background_0 = pygame.image.load("/home/catreson/WUTRPi/res/back_0.png").convert()
screen_background_1 = pygame.image.load("/home/catreson/WUTRPi/res/back_1.png").convert()
screen_loading = pygame.image.load("/home/catreson/WUTRPi/res/wut.png").convert()
listen_topic = "bike/display/#"


def sec2min(sectime):
    fsectime = float(sectime)
    minutes = int(fsectime / 60)
    seconds = round(fsectime - 60 * minutes, 3)
    if seconds < 10:
        return str(minutes) + ':0' + str(seconds)
    return str(minutes) + ':' + str(seconds)


def on_message(client, userdata, message):
    mesenge = str(message.payload.decode("utf-8"))
    print("message received ", mesenge)
    print("message topic=", message.topic)
    if message.topic == 'bike/display/gps':
        msg = mesenge.split(',')
        global laptime
        global lapno
        global delta
        try:
            if msg[2] != ' susp_f':
                delt1 = msg[5]
                lapno = msg[3]
                laptim1 = msg[4]
                if float(delt1) < 1000000:
                    delta = delt1
                if float(laptim1) < 1000000:
                    laptime = laptim1
        except:
            print('err')
    print('mqtt')



cm = SHM()
data1 = cm.read_bulk()

try:
    print('MQTT init')
    mqtit = MQTT_CLIENT(client_id='display')
    print('MQTT created')
    logging.info('Created client')
    mqtit.subscribe(listen_topic, on_message)
    print('MQTT set')
    logging.info('Client connected')
except:
    sys.exit('No connection to MQTT broker')

#GPIO.setmode(GPIO.BCM)
#GPIO.setwarnings(False)
#GPIO.setup(21, GPIO.OUT)

# loading screen
for i in range(40):
    screen_loading.set_alpha(i)
    screen.blit(screen_loading, (0, 78))
    pygame.display.flip()
    time.sleep(0.05)
time.sleep(1)
screen.blit(screen_background_0, (0, 0))
pygame.display.flip()

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            finger = pygame.mouse.get_pos()
            if 700 <= finger[0] <= 800 and 0 <= finger[1] <= 100:
                screen_mode = screen_mode * (-1)
            if screen_mode == -1 and 0 < finger[0] < 160 and 320 < finger[1] < 480:
                inversion = inversion * (-1)
            if screen_mode == 1 and 400 < finger[0] < 600:
                if 30 < finger[1] < 180:
                    fc_count = fc_count + 1
                    if fc_count > 5:
                        mqtit.send('bike/correction/susp', 'susp_f')
                        fc_count = 0
                if 330 < finger[1] < 480:
                    rc_count = rc_count + 1
                    if rc_count > 5:
                        mqtit.send('bike/correction/susp', 'susp_r')
                        rc_count = 0
                if 180 < finger[1] < 330:
                    st_count = st_count + 1
                    if st_count > 5:
                        mqtit.send('bike/correction/susp', 'steer_angle')
                        st_count = 0
            if screen_mode == 1 and 600 < finger[0]:
                if 330 < finger[1] < 480:
                    pb_count = pb_count + 1
                    if pb_count > 5:
                        mqtit.send('bike/correction/susp', 'p_brake')
                        pb_count = 0

    if screen_mode == -1:
        screen.blit(screen_background_0, (0, 0))

        img = font1.render(sec2min(laptime), True, cfont0)
        screen.blit(img, (off2, offtop0))

        img = font1.render(str(delta), True, cfont0)
        screen.blit(img, (off2, offtop0 + height2))

        img = font1.render(str(round(data1[0])), True, cfont0)
        screen.blit(img, (off2 + 115, offtop0 + 2 * height2))

        img = font2.render(str(round(data1[7], 2)), True, cfont0)
        screen.blit(img, (off1 + 610, offtop0 + 80))

        img = font2.render(str(data1[4]), True, cfont0)
        screen.blit(img, (off1 + 645, offtop0 + 2 * height2 + 20))

        if inversion == 1:
            pixels = pygame.surfarray.pixels2d(screen)
            pixels ^= 2 ** 32 - 1
            del pixels

    if screen_mode == 1:
        screen.blit(screen_background_1, (0, 0))

        img = font2.render(str(int(data1[0])), True, cfont1)
        screen.blit(img, (off1, offtop + off1))

        img = font2.render(str(data1[10]), True, cfont1)
        screen.blit(img, (off1, offtop + off1 + height1))

        img = font2.render(str(data1[8]), True, cfont1)
        screen.blit(img, (off1, offtop + off1 + 2 * height1))

        img = font2.render(str(data1[1]), True, cfont1)
        screen.blit(img, (off1 + width1, offtop + off1))

        img = font2.render(str(data1[5]), True, cfont1)
        screen.blit(img, (off1 + width1, offtop + off1 + height1))

        img = font2.render(str(int(data1[9])), True, cfont1)
        screen.blit(img, (off1 + width1, offtop + off1 + 2 * height1))

        # susp_f
        img = font2.render(str(round(data1[2])), True, cfont1)
        screen.blit(img, (off1 + 2 * width1, offtop + off1))

        img = font2.render(str(data1[4]), True, cfont1)
        screen.blit(img, (off1 + 2 * width1, offtop + off1 + height1))

        img = font2.render(str(round(data1[6])), True, cfont1)
        screen.blit(img, (off1 + 2 * width1, offtop + off1 + 2 * height1))

        img = font2.render(str(round(data1[3], 2)), True, cfont1)
        screen.blit(img, (off1 + 3 * width1, offtop + off1))

        img = font2.render(str(data1[7]), True, cfont1)
        screen.blit(img, (off1 + 3 * width1, offtop + off1 + height1))

        img = font2.render(str(round(data1[11], 1)), True, cfont1)
        screen.blit(img, (off1 + 3 * width1, offtop + off1 + 2 * height1))

        pygame.draw.rect(screen, rpm_col, pygame.Rect(0, 0, data1[0] / rpm_max * 800, 60))

    pygame.display.flip()
    fpsClock.tick(FPS)
GPIO.cleanup()
pygame.quit()
