import os
import time
import logging
from multiprocessing import Process

DISPLAY_STOP_FLAG = '/tmp/wutrpi_display_stopped'
RESTART_ECU_FLAG = '/tmp/wutrpi_restart_ecu'

pyro_list = [['pyro_fc', 0x5a],
  ['pyro_fr', 0x6a],
  ['pyro_fl', 0x7a],
  ['pyro_rc', 0x4c],
  ['pyro_rr', 0x6c],
  ['pyro_rl', 0x5c]]


offline = 0

def ECU_thread():
    global offline
    from rs232 import ECU
    ecu = ECU()
    ecu.reading_loop()

def susp_thread():
    global offline
    from susp import SUSPENSION
    from common import READ_TRIGGER
    susp = SUSPENSION(offline = offline)
    susp_trigger = READ_TRIGGER(frequency = 200, func = susp.read_data)

def giro_thread():
    global offline
    from gyro import GIROSCOPES
    from common import READ_TRIGGER
    giro = GIROSCOPES(address = [0x68], bus = 1, offline = offline)
    giro_trigger = READ_TRIGGER(frequency = 50, func = giro.read_data)

def pyro_thread():
    global offline
    global pyro_list
    from pyro import PYROMETERS
    from common import READ_TRIGGER
    pyro = PYROMETERS(pyrometers_in_use = pyro_list, busnum = 0, offline = offline)
    pyro_trigger = READ_TRIGGER(frequency = 1, func = pyro.read_data)

def gps_thread():
    global offline
    from gps import GPS
    gps = GPS(busnum = 1, address = 0x42, offline = offline)
    gps.run()

def leds_thread():
    global offline
    from leds import run_leds
    run_leds(offline = offline)

def display_thread():
    global offline
    from disp4 import run_display
    run_display(offline = offline)

def logger_thread():
    from logger import LOGGER
    from common import READ_TRIGGER
    logger = LOGGER()
    logger_trigger = READ_TRIGGER(frequency = 200, func = logger.log_row)


proces_dict = {
  'ecu_proc': ECU_thread,
  'susp_proc': susp_thread,
  'giro_proc': giro_thread,
  'pyro_proc': pyro_thread,
  'gps_proc': gps_thread,
  'leds_proc': leds_thread,
  'logger_proc': logger_thread,
  'display_proc': display_thread}

if __name__ == "__main__":
    if os.path.exists(DISPLAY_STOP_FLAG):
        os.remove(DISPLAY_STOP_FLAG)
    if os.path.exists(RESTART_ECU_FLAG):
        os.remove(RESTART_ECU_FLAG)

    P = []
    ind = 0
    for proces_name in proces_dict.keys():
        try:
            p1 = Process(target = proces_dict[proces_name], name = proces_name)
            p1.start()
            P.append((proces_name, p1))
            ind += 1
        except:
            logging.warning(f'{proces_name} not started')

    while True:
        if os.path.exists(RESTART_ECU_FLAG):
            os.remove(RESTART_ECU_FLAG)
            for (nam, proces) in list(P):
                if nam == 'ecu_proc':
                    logging.warning('ecu_proc restart requested')
                    P.remove((nam, proces))
                    if proces.is_alive():
                        proces.terminate()
                        proces.join(timeout=5)
                    p = Process(target = proces_dict[nam], name = nam)
                    p.start()
                    logging.warning('ecu_proc restarted on request')
                    P.append((nam, p))

        for (nam, proces) in list(P):
            if proces.is_alive():
                logging.info(f'{nam} is alive')
            elif nam == 'display_proc' and os.path.exists(DISPLAY_STOP_FLAG):
                logging.info('display_proc intentionally stopped, not resurrecting')
                P.remove((nam, proces))
            else:
                logging.warning(f'{nam} is dead')
                P.remove((nam, proces))
                p = Process(target = proces_dict[nam], name = nam)
                p.start()
                logging.warning(f'{nam} is ressurected')
                P.append((nam, p))
        time.sleep(10)


