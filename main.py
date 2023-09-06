import time
import logging
from multiprocessing import Process
from rs232 import ECU
from susp import SUSPENSION
from pyro import PYROMETERS
from gyro import GIROSCOPES
from common import READ_TRIGGER

pyro_list = [['pyro_fc', 0x5a],
  ['pyro_fr', 0x6a],
  ['pyro_fl', 0x7a]]

  
offline = 0

def ECU_thread():
    global offline
    ecu = ECU()
    ecu.reading_loop()
    
def susp_thread():
    global offline
    susp = SUSPENSION(offline = offline) 
    susp_trigger = READ_TRIGGER(frequency = 50, func = susp.read_data)
    
def giro_thread():
    global offline
    giro = GIROSCOPES(address = 0x68, bus = 1, offline = offline)
    giro_trigger = READ_TRIGGER(frequency = 10, func = giro.read_data)
    
def pyro_thread():
    global offline
    global pyro_list
    pyro = PYROMETERS(pyrometers_in_use = pyro_list, busnum = 0, offline = offline)
    pyro_trigger = READ_TRIGGER(frequency = 1, func = pyro.read_data)


proces_dict = {
  'ecu_proc': ECU_thread,
  'susp_proc': susp_thread,
  'giro_proc': giro_thread,
  'pyro_proc': pyro_thread}

if __name__ == "__main__":
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
        for (nam, proces) in P:
            if proces.is_alive():
                logging.info(f'{nam} is alive')
            else:
                logging.warning(f'{nam} is dead')
                P.remove((nam, proces))
                p = Process(target = proces_dict[nam], name = nam)
                p.start()
                logging.warning(f'{nam} is ressurected')
                P.append(p)
        time.sleep(10)
                
    