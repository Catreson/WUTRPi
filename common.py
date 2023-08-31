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

    mqtt_file = None 
    
    def __init__(self, path = '/home/catreson/dane_esp_write/mqtt_csv{filet}', filename = 'mqtt_csv{tim}.csv'):
        filename.format(tim = time.time())
        path.format(filet = filename)
        patho = path + str(round(time.time(),0)) + '.csv'
        self.mqtt_file = open(patho, 'w')
        
    def save(self, event):
        self.mqtt_file.write(f'{event}\n')

class SHM(): #metaclass=Singleton):

    names_dict = defaultdict(lambda : 16)

    def fill_names_dict(self):
        with open('res/sensors.csv', 'r') as filet:
            sensor_number = 0
            for sensor in filet:
                self.names_dict[sensor] = sensor_number
                sensor_number += 1

    def __init__(self):
        self.fill_names_dict()
        self.a = np.array([1.0] * len(self.names_dict))
        print(self.names_dict)
        try:
            self.disp_shm = shared_memory.SharedMemory(create=True, size=self.a.nbytes, name='disp_shm')
            self.b = np.ndarray(self.a.shape, dtype=self.a.dtype, buffer=self.disp_shm.buf)
            self.b[:] = self.a[:]
        except:
            self.disp_shm = shared_memory.SharedMemory(name='disp_shm')
            resource_tracker.unregister(self.disp_shm._name, 'shared_memory')
            self.b = np.ndarray(self.a.shape, dtype=self.a.dtype, buffer=self.disp_shm.buf)

    def save(self, name, var):
        self.b[self.names_dict[name]] = var

    def read(self, name): 
        return self.b[self.names_dict[name]]
            
    def read_bulk(self):
        return self.b[:]

class MQTT_CLIENT():
    
    def send_mqtt(self, topic, event):
        self.client.publish(topic, event)
    
    def send_file(self, topic, event):
        self.offline_file.save(event)
        
    save_mode = {
      0 : send_mqtt,
      1 : send_file}
      
    def __init__(self, client_id, offline = 0):
        logging.info('Creating client')
        self.client = mqtt.Client(client_id, protocol = mqtt.MQTTv311)
        self.client.connect('localhost')
        logging.info('Connceted to localhost')
        self.is_offline = offline
        self.offline_file = SAVE_CSV()
        
    def send(self, topic, event):
        self.save_mode[self.is_offline](self, topic = topic, event = event)
           
    def subscribe(self, topic, func):
        print('Subscribing')
        self.client.subscribe(topic)
        print('Subscribed, assigning func')
        self.client.on_message = func
        print('Assigned, looping')
        self.client.loop_start()
        
if __name__ == "__main__":
    print("No use like that")
    mqtit = MQTT_CLIENT(client_id = 'someting', offline = 0)
    #mqtit.subscribe(topic = 'bike/correction/susp', func = print("mqtit"))
    print('Connected')

    shim = SHM()
    