import pygame
import os
import time
from common import SHM, MQTT_CLIENT
import logging
import sys
import shutil
import subprocess

REPO_DIR = '/home/catreson/WUTRPi'
INSTALL_RC_LOCAL = f'{REPO_DIR}/deploy/install_rc_local.sh'
LX_SCRIPT = '/home/catreson/lx.sh'
DISPLAY_STOP_FLAG = '/tmp/wutrpi_display_stopped'
RESTART_ECU_FLAG = '/tmp/wutrpi_restart_ecu'
SUSP_CORRECTION_CODES = {'susp_f': 1, 'susp_r': 2, 'p_brake': 3, 'steer_angle': 4}


def _git_remote_url():
    try:
        result = subprocess.run(['git', '-C', REPO_DIR, 'remote', 'get-url', 'origin'],
                                 capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _git_branch_name():
    try:
        result = subprocess.run(['git', '-C', REPO_DIR, 'rev-parse', '--abbrev-ref', 'HEAD'],
                                 capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return 'test'


def _git_commit_hash():
    try:
        result = subprocess.run(['git', '-C', REPO_DIR, 'rev-parse', '--short', 'HEAD'],
                                 capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return 'unknown'


def _log_failure(label, result):
    logging.warning(f'{label} failed (exit {result.returncode}): stdout={result.stdout!r} stderr={result.stderr!r}')


def _reclone_fresh():
    """Local repo looks corrupt (e.g. from a power-loss during a write on the SD card) -
    throw it away and clone a fresh copy instead of trying to repair it in place."""
    url = _git_remote_url()
    if not url:
        return 'Repo unreadable and remote URL unknown - needs manual fix'
    branch = _git_branch_name()
    tmp_dir = f'{REPO_DIR}_freshclone'
    shutil.rmtree(tmp_dir, ignore_errors=True)
    clone = subprocess.run(['git', 'clone', '--branch', branch, '--single-branch', url, tmp_dir],
                            capture_output=True, text=True, timeout=120)
    if clone.returncode != 0:
        _log_failure('git clone', clone)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return f'Re-clone failed: {clone.stderr.strip()[:60]} (see main_log.txt)'
    try:
        shutil.rmtree(REPO_DIR)
        shutil.move(tmp_dir, REPO_DIR)
    except OSError as exc:
        logging.warning(f'Failed to swap in fresh clone: {exc}')
        return f'Failed to swap in fresh clone: {exc}'
    return None


def run_update():
    try:
        fetch = subprocess.run(['git', '-C', REPO_DIR, 'fetch', 'origin'], capture_output=True, text=True, timeout=30)
        synced = False
        if fetch.returncode == 0:
            branch_name = _git_branch_name()
            reset = subprocess.run(['git', '-C', REPO_DIR, 'reset', '--hard', f'origin/{branch_name}'],
                                    capture_output=True, text=True, timeout=30)
            synced = reset.returncode == 0
            if not synced:
                _log_failure('git reset --hard', reset)
        else:
            _log_failure('git fetch', fetch)
        if not synced:
            error = _reclone_fresh()
            if error:
                return error
        install = subprocess.run(['sudo', 'sh', INSTALL_RC_LOCAL], capture_output=True, text=True, timeout=30)
        if install.returncode != 0:
            _log_failure('install_rc_local.sh', install)
            return f'rc.local install failed: {install.stderr.strip()[:60]} (see main_log.txt)'
        return 'Updated OK'
    except Exception as exc:
        return f'Update error: {exc}'[:80]


def run_close():
    try:
        with open(DISPLAY_STOP_FLAG, 'w') as f:
            f.write('stopped')
    except OSError as exc:
        logging.warning(f'Failed to write display stop flag: {exc}')
    try:
        subprocess.Popen([LX_SCRIPT], start_new_session=True)
    except OSError as exc:
        logging.warning(f'Failed to launch lx.sh: {exc}')


def request_ecu_restart():
    try:
        with open(RESTART_ECU_FLAG, 'w') as f:
            f.write('restart')
    except OSError as exc:
        logging.warning(f'Failed to write ECU restart flag: {exc}')


def run_display(offline=0):
    os.environ["DISPLAY"] = ":0"
    pygame.init()

    laptime = 0.0
    delta = 0.0
    lapno = 0
    rtk_flag = (255, 0, 0)
    engine_mode = "A"
    water_err = False

    engine_mode_dict = { 'P' : (240, 240, 0), 'L' : (0, 240, 0), 'A' : (240, 0, 0)}
    err_col = (240, 0, 0)

    # display configuration -------------------
    display_resolution = [800, 480]
    inversion = -1
    screen_mode = 0
    race_mode = 0
    rpm_max = 12000
    rpm = 1350

    # offsets
    width1 = 800 / 4
    height1 = 420 / 3
    offtop = 100
    off1 = 15
    offtop0 = 25
    off2 = 115
    height2 = int(480 / 3)

    # click counts
    fc_count = 0
    rc_count = 0
    st_count = 0
    pb_count = 0
    splt_count = 0
    update_count = 0
    close_count = 0
    ecu_restart_count = 0
    shutdown_count = 0
    update_status = ''
    commit_hash = _git_commit_hash()

    #splits names fetch
    split_dict = {}
    pather = '/home/catreson/dane_esp_read/'
    entries = os.listdir(pather)
    indexer = 0
    for split in entries:
        if 'splits_' in split:
            nam = split.split('.')
            split_dict[indexer] = [nam[0], split]
            indexer += 1

    split_count = indexer
    current_split = 0

    # font setup
    cfont0 = (240, 240, 240)
    cfont1 = (0, 0, 0)
    rpm_col = (200, 200, 200)
    font0 = pygame.font.SysFont(None, 320)
    font1 = pygame.font.SysFont(None, 180)
    font2 = pygame.font.SysFont(None, 100)
    font3 = pygame.font.SysFont(None, 60)

    FPS = 10
    fpsClock = pygame.time.Clock()
    # end of display configuration -------------


    # end GPIO config

    screen = pygame.display.set_mode(display_resolution, pygame.FULLSCREEN)
    # screen = pygame.display.set_mode(display_resolution)
    pygame.display.set_caption('Display')
    screen_background_0 = pygame.image.load("/home/catreson/WUTRPi/res/back_0.png").convert()
    screen_background_1 = pygame.image.load("/home/catreson/WUTRPi/res/back_1.png").convert()
    screen_background_2 = pygame.image.load("/home/catreson/WUTRPi/res/back_2.png").convert()
    screen_background_3 = pygame.image.load("/home/catreson/WUTRPi/res/back_3.png").convert()
    screen_mcshow = pygame.image.load("/home/catreson/WUTRPi/res/mcshow.jpg").convert()
    screen_loading = pygame.image.load("/home/catreson/WUTRPi/res/wut.png").convert()
    listen_topic = "bike/display/gps"
    pygame.mouse.set_visible(False)


    def sec2min(sectime):
        fsectime = float(sectime)
        minutes = int(fsectime / 60)
        seconds = round(fsectime - 60 * minutes, 3)
        if seconds < 10:
            return str(minutes) + ':0' + str(seconds)
        return str(minutes) + ':' + str(seconds)


    def on_message(client, userdata, message):
        nonlocal laptime, lapno, delta
        mesenge = str(message.payload.decode("utf-8"))
        print("message received ", mesenge)
        print("message topic=", message.topic)
        if message.topic == 'bike/display/gps':
            msg = mesenge.split(',')
            try:
                if msg[2] != ' susp_f':
                    delt1 = msg[5]
                    lapno = msg[3]
                    laptim1 = msg[4]
                    if float(delt1) < 1000000:
                        delta = float(delt1)
                    if float(laptim1) < 1000000:
                        laptime = laptim1
            except:
                print('err')
        print('mqtt')



    cm = SHM()
    data1 = cm.read_bulk()
    idx_rtk = cm.names_dict['rtk_flag']
    idx_water = cm.names_dict['water_err']

    try:
        print('MQTT init')
        mqtit = MQTT_CLIENT(client_id='display', offline=offline)
        print('MQTT created')
        logging.info('Created client')
        mqtit.subscribe(listen_topic, on_message)
        print('MQTT set')
        logging.info('Client connected')
    except:
        sys.exit('No connection to MQTT broker')

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
        rtk_flag = (0, 240, 0) if data1[idx_rtk] else (240, 0, 0)
        water_err = bool(data1[idx_water])
        engine_mode = 'A'
        race_mode = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                finger = pygame.mouse.get_pos()

                if 0 <= finger[1] <= 100:
                    if 700 <= finger[0]:
                        screen_mode = (screen_mode + 1) % 5
                    elif finger[0] <= 100:
                        screen_mode = (screen_mode - 1) % 5

                if screen_mode == 0 and 0 < finger[0] < 160 and 320 < finger[1] < 480:
                    inversion = inversion * (-1)

                elif screen_mode == 0 and water_err and 660 <= finger[0] <= 800 and 250 <= finger[1] <= 330:
                    ecu_restart_count = ecu_restart_count + 1
                    if ecu_restart_count > 5:
                        request_ecu_restart()
                        ecu_restart_count = 0

                elif screen_mode == 1:
                    if finger[0] < 200:
                            if 180 < finger[1] < 330:
                                st_count = st_count + 1
                                if st_count > 5:
                                    cm.save('susp_correction_request', SUSP_CORRECTION_CODES['steer_angle'])
                                    st_count = 0

                    elif 400 < finger[0] < 600:
                        if 30 < finger[1] < 180:
                            fc_count = fc_count + 1
                            if fc_count > 5:
                                cm.save('susp_correction_request', SUSP_CORRECTION_CODES['susp_f'])
                                fc_count = 0

                        if 330 < finger[1] < 480:
                            rc_count = rc_count + 1
                            if rc_count > 5:
                                cm.save('susp_correction_request', SUSP_CORRECTION_CODES['susp_r'])
                                rc_count = 0

                    elif 600 < finger[0]:
                        if 330 < finger[1] < 480:
                            pb_count = pb_count + 1
                            if pb_count > 5:
                                cm.save('susp_correction_request', SUSP_CORRECTION_CODES['p_brake'])
                                pb_count = 0


                elif screen_mode == 2:
                    if 300 <= finger[1] <= 360:
                        if 60 <= finger[0] <= 240:
                            current_split = (current_split - 1) % split_count
                        elif 560 <= finger[0] <= 740:
                            current_split = (current_split + 1) % split_count
                        elif 300 <= finger[0] <= 480:
                            splt_count = splt_count + 1
                            if splt_count > 5:
                                shutil.copy(f'{pather}{split_dict[current_split][1]}', f'{pather}splits.csv')
                                screen.blit(screen_background_3, (0, 0))
                                img = font1.render('Copied!', True, (255, 255, 255))
                                screen.blit(img, (140, 100))
                                pygame.display.flip()
                                splt_count = 0
                                time.sleep(3)

                elif screen_mode == 4:
                    if 100 <= finger[0] <= 700:
                        if 100 <= finger[1] <= 210:
                            update_count = update_count + 1
                            if update_count > 5:
                                update_status = run_update()
                                update_count = 0
                                commit_hash = _git_commit_hash()
                        elif 220 <= finger[1] <= 330:
                            close_count = close_count + 1
                            if close_count > 5:
                                run_close()
                                running = False
                        elif 340 <= finger[1] <= 450:
                            shutdown_count = shutdown_count + 1
                            if shutdown_count > 5:
                                screen.fill((0, 0, 0))
                                img = font1.render('You can turn off', True, (255, 255, 255))
                                screen.blit(img, (60, 180))
                                img = font1.render('computer now', True, (255, 255, 255))
                                screen.blit(img, (100, 260))
                                pygame.display.flip()
                                subprocess.run(['sudo', 'shutdown', '-h', 'now'])
                                while True:
                                    time.sleep(60)

        if screen_mode == 0:
            if race_mode == 0:
                screen.blit(screen_background_0, (0, 0))

                img = font1.render(sec2min(laptime), True, cfont0)
                screen.blit(img, (off2, offtop0))

                img = font1.render("%.3f" %delta, True, cfont0)
                screen.blit(img, (off2, offtop0 + height2))

                img = font1.render("%.0f" %data1[0], True, cfont0) # rpm
                screen.blit(img, (off2 + 115, offtop0 + 2 * height2))

                img = font3.render("%.2f" %data1[7], True, cfont0) # lambda
                screen.blit(img, (off1 + 665, offtop0 - 10))

                if water_err:
                    img = font3.render("ERR", True, err_col) # water temp read unavailable
                else:
                    img = font3.render("RTK", True, rtk_flag) # rtk indicator
                screen.blit(img, (off1 + 665, offtop0 + 245))

                img = font1.render(engine_mode, True, engine_mode_dict.get(engine_mode, cfont0))
                screen.blit(img, (off1 + 665, offtop0 + 80))

                img = font2.render("%.0f" %data1[4], True, cfont0) # h2o temp
                screen.blit(img, (off1 + 655, offtop0 + 2 * height2 + 20))

                if inversion == 1:
                    pixels = pygame.surfarray.pixels2d(screen)
                    pixels ^= 2 ** 32 - 1
                    del pixels

            else:
                screen.blit(screen_background_2, (0, 0))

                img = font0.render("%.1f" %data1[12], True, cfont0) # speed
                screen.blit(img, (off2 + 50, offtop0 + 50))

                img = font1.render("%.0f" %data1[0], True, cfont0) # rpm
                screen.blit(img, (off2 + 115, offtop0 + 2 * height2))

                img = font3.render("%.2f" %data1[7], True, cfont0) # lambda
                screen.blit(img, (off1 + 665, offtop0 - 10))

                if water_err:
                    img = font3.render("ERR", True, err_col) # water temp read unavailable
                else:
                    img = font3.render("RTK", True, rtk_flag) # rtk indicator
                screen.blit(img, (off1 + 665, offtop0 + 245))

                img = font1.render(engine_mode, True, engine_mode_dict.get(engine_mode, cfont0))
                screen.blit(img, (off1 + 665, offtop0 + 80))

                img = font2.render("%.0f" %data1[4], True, cfont0) # h2o temp
                screen.blit(img, (off1 + 655, offtop0 + 2 * height2 + 20))

                if inversion == 1:
                    pixels = pygame.surfarray.pixels2d(screen)
                    pixels ^= 2 ** 32 - 1
                    del pixels

        elif screen_mode == 1:
            screen.blit(screen_background_1, (0, 0))

            img = font2.render(str(int(data1[0])), True, cfont1)
            screen.blit(img, (off1, offtop + off1))

            img = font2.render("%.1f" % data1[16], True, cfont1)
            screen.blit(img, (off1, offtop + off1 + height1))

            img = font2.render(str(data1[10]), True, cfont1)
            screen.blit(img, (off1, offtop + off1 + 2 * height1))

            img = font2.render(str(data1[1]), True, cfont1)
            screen.blit(img, (off1 + width1, offtop + off1))

            img = font2.render(str(data1[5]), True, cfont1)
            screen.blit(img, (off1 + width1, offtop + off1 + height1))

            img = font2.render(str(int(data1[9])), True, cfont1)
            screen.blit(img, (off1 + width1, offtop + off1 + 2 * height1))

            # susp_f
            img = font2.render("%.1f" % data1[2], True, cfont1)
            screen.blit(img, (off1 + 2 * width1, offtop + off1))

            img = font2.render(str(data1[4]), True, cfont1)
            screen.blit(img, (off1 + 2 * width1, offtop + off1 + height1))

            img = font2.render("%.1f" % data1[6], True, cfont1)
            screen.blit(img, (off1 + 2 * width1, offtop + off1 + 2 * height1))

            img = font2.render("%.1f" % data1[3], True, cfont1)
            screen.blit(img, (off1 + 3 * width1, offtop + off1))

            img = font2.render("%.2f" % data1[7], True, cfont1)
            screen.blit(img, (off1 + 3 * width1, offtop + off1 + height1))

            img = font2.render("%.1f" % data1[11], True, cfont1)
            screen.blit(img, (off1 + 3 * width1, offtop + off1 + 2 * height1))

            pygame.draw.rect(screen, rpm_col, pygame.Rect(0, 0, data1[0] / rpm_max * 800, 60))

        elif screen_mode == 2:
            screen.blit(screen_background_3, (0, 0))

            img = font3.render(split_dict[current_split][0], True, (255,255,255))
            screen.blit(img, (140, 100))

            pygame.draw.rect(screen, (200, 200, 200), pygame.Rect(60, 300, 180, 60))
            pygame.draw.polygon(screen, (40, 40, 40), ((120, 330), (180, 310), (180, 350)))

            pygame.draw.rect(screen, (200, 200, 200), pygame.Rect(560, 300, 180, 60))
            pygame.draw.polygon(screen, (40, 40, 40), ((680, 330), (620, 310), (620, 350)))

            pygame.draw.rect(screen, (0, 200, 0), pygame.Rect(300, 300, 180, 60))

        elif screen_mode == 3:
            screen.blit(screen_mcshow, (0, 0))

        elif screen_mode == 4:
            screen.fill((20, 20, 20))

            pygame.draw.rect(screen, (60, 60, 60), pygame.Rect(100, 100, 600, 110))
            img = font2.render('UPDATE', True, (255, 255, 255))
            screen.blit(img, (260, 130))

            pygame.draw.rect(screen, (90, 30, 30), pygame.Rect(100, 220, 600, 110))
            img = font2.render('CLOSE', True, (255, 255, 255))
            screen.blit(img, (280, 250))

            pygame.draw.rect(screen, (30, 30, 30), pygame.Rect(100, 340, 600, 110))
            img = font2.render('SHUTDOWN', True, (255, 255, 255))
            screen.blit(img, (185, 370))

            img = font3.render(f'commit: {commit_hash}', True, (150, 150, 150))
            screen.blit(img, (20, 20))

            if update_status:
                img = font3.render(update_status, True, (255, 255, 0))
                screen.blit(img, (20, 60))

        pygame.display.flip()
        fpsClock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    run_display()
