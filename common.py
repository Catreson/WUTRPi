import numpy as np
from multiprocessing import shared_memory, resource_tracker
import time
from threading import Lock, Thread
import paho.mqtt.client as mqtt
from collections import defaultdict
import logging

class Singleton(type):

    _instances = {}

    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):

        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class READ_TRIGGER():
    
    def timer_tick(self, frequency):
        t = time.time()
        while True:
            t += 1/frequency
            yield max(t - time.time(),0)
    
    def __init__(self, frequency, func):
        self.step = self.timer_tick(frequency)
        while True:
            time.sleep(next(self.step))
            func()
            

class SAVE_CSV(metaclass=Singleton):

    def __init__(self, client_id = 'mqtt', path = '/home/catreson/dane_esp_write/'):
        filename = f'{client_id}_csv_{round(time.time())}.csv'
        self.mqtt_file = open(f'{path}{filename}', 'w')

    def save(self, event):
        self.mqtt_file.write(f'{event}\n')
        self.mqtt_file.flush()

class SHM():

    def fill_names_dict(self):
        self.names_dict = defaultdict(lambda: self.names_dict.get('err', 0))
        with open('/home/catreson/WUTRPi/res/sensors.csv', 'r') as filet:
            sensor_number = 0
            for sensor in filet:
                self.names_dict[sensor.strip()] = sensor_number
                sensor_number += 1

    def __init__(self):
        self.fill_names_dict()
        self.a = np.array([1.0] * len(self.names_dict))
        print(self.names_dict)
        try:
            self.disp_shm = shared_memory.SharedMemory(create=True, size=self.a.nbytes, name='disp_shm')
            self.b = np.ndarray(self.a.shape, dtype=self.a.dtype, buffer=self.disp_shm.buf)
            self.b[:] = self.a[:]
        except FileExistsError:
            self.disp_shm = shared_memory.SharedMemory(name='disp_shm')
            if self.disp_shm.size != self.a.nbytes:
                logging.warning('Stale disp_shm size does not match sensors.csv, recreating')
                self.disp_shm.close()
                self.disp_shm.unlink()
                self.disp_shm = shared_memory.SharedMemory(create=True, size=self.a.nbytes, name='disp_shm')
                self.b = np.ndarray(self.a.shape, dtype=self.a.dtype, buffer=self.disp_shm.buf)
                self.b[:] = self.a[:]
            else:
                resource_tracker.unregister(self.disp_shm._name, 'shared_memory')
                self.b = np.ndarray(self.a.shape, dtype=self.a.dtype, buffer=self.disp_shm.buf)
        print('SHM init complete')

    def save(self, name, var):
        if name not in self.names_dict:
            logging.warning(f'Unknown SHM sensor name "{name}", writing to err slot')
        self.b[self.names_dict[name]] = var

    def read(self, name):
        if name not in self.names_dict:
            logging.warning(f'Unknown SHM sensor name "{name}", reading err slot')
        return self.b[self.names_dict[name]]
            
    def read_bulk(self):
        return self.b[:]

class MQTT_CLIENT():

    timestam = 0

    def __init__(self, client_id, offline = 0):
        logging.info('Creating client')
        self.client = mqtt.Client(client_id, protocol = mqtt.MQTTv311)
        self.client.connect('localhost')
        self.client.loop_start()
        logging.info('Connceted to localhost')
        self.is_offline = offline
        if offline == 1:
            self.offline_file = SAVE_CSV(client_id)
        with open('/home/catreson/skrypty/timestamp.txt','r') as filet:
            tmp = filet.readline()
            tmp.strip()
            self.timestam = float(tmp)

    def send(self, topic, event):
        if self.is_offline == 1:
            self.offline_file.save(f'{topic},{event}')
        else:
            self.client.publish(topic, event)


    def subscribe(self, topic, func):
        print('Subscribing')
        self.client.subscribe(topic)
        print('Subscribed, assigning func')
        self.client.on_message = func
        print('Assigned')
        
if __name__ == "__main__":
    print("No use like that")
    mqtit = MQTT_CLIENT(client_id = 'someting', offline = 0)
    #mqtit.subscribe(topic = 'bike/correction/susp', func = print("mqtit"))
    print('Connected')

    shim = SHM()
    