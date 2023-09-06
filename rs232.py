import serial
import binascii
import time
import sys
from common import SHM, MQTT_CLIENT
from collections import defaultdict
import logging

class ECU():

    def temp(self, x):
        y=x/10 -100
        return y

    def temp_water(self, x):
        self.succes_read = time.time()
        y= x/10 -100
        if y > 120 or y < 5:
            self.synchronize_read()
        self.last_temp = time.time()
        return y

    def speed(self, x):
        y = x/10
        return y

    def bar(self, x):
        y=x/1000
        return y

    def mbar(self, x):
        y=x
        return y

    def volt(self, x):
        y=x/100
        return y

    succes_read = time.time()
    
    sensor_list=[[1,'rpm',10,mbar],
    [5,'wheel_f_ecu',10,speed],
    [9,'p_oil',5,bar],
    [13,'t_oil',2,temp],
    [17,'t_water',2,temp_water],
    [21,'p_fuel',5,bar],
    [33,'v_bat',5,volt],
    [45,'tps',10,speed],
    [69,'p_manifold',10,mbar],
    [97,'air_t',2,temp],
    [101,'egt',2,temp],
    [105,'lambda',10,bar],
    [109,'t_fuel',2,temp],
    [113,'gear',5,mbar],
    [12,'cos',5,mbar]] #nie wiem co to, ja tez nie
    
    sensor_dict = defaultdict(lambda : [666, 'err', 0, lambda s, x: 0])
    
    last_temp = 0    
    write_topic = 'bike/sensor/ecu'
    
    def __init__(self, port = "/dev/ttyAMA1", baudrate = 19200, offline = 0):
        self.ser = serial.Serial(port, baudrate)
        try:
            self.cm = SHM()
        except:
            sys.exit('No shared memory access')
        try:
            self.mqtt = MQTT_CLIENT(client_id = 'suspension', offline = offline)
            #self.mqtt.subscribe(self.listen_topic, correction)
        except:
            sys.exit('No connection to MQTT broker')
        self.fill_sensor_dict()

    def fill_sensor_dict(self):
        for sensor in self.sensor_list:
            self.sensor_dict[sensor[0]] = sensor

    def synchronize_read(self):
        stri=binascii.b2a_hex(self.ser.read(size=1)).decode('utf-8')
        while stri != "a3":
	        stri=binascii.b2a_hex(self.ser.read(size=1)).decode('utf-8')
        self.ser.read(size=3)
        logging.info('Synchronized input')

    def reading_loop(self):
        while True:
            kanal = int(binascii.b2a_hex(self.ser.read(size=1)),16)
            self.ser.read(size=1)
            value = int(binascii.b2a_hex(self.ser.read(size=2)),16)
            self.ser.read(size=1)
            sensor = self.sensor_dict[kanal]
            calc = sensor[3](self, x = value)
            self.cm.save(name = sensor[1], var = calc)
            prin(f"{sensor[1]},{time.time()},{calc},bike/sensor/ecu,double")
            self.mqtt.send(topic = self.write_topic, event = f"{sensor[1]},{time.time()},{calc},bike/sensor/ecu,double")
            if time.time() - self.succes_read > 10:
                self.synchronize_read()
            
if __name__ == "__main__":
    eku = ECU()
    eku.reading_loop()