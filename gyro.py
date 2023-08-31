import math
import time
from mpu6050 import mpu6050
import io
import logging
from .lib.common import MQTT_CLIENT, SHM, READ_TRIGGER


class GIROSCOPES:

    address = 0x68   
    write_topic = 'bike/sensor/imu'
    
    def __init__(self, address = 0x68, bus = 1, offline = 0):
        self.gyro = mpu6050(address, bus)
        self.gyro.set_accel_range(accel_range = self.gyro.ACCEL_RANGE_4G)
        if self.gyro.read_accel_range() != self.gyro.ACCEL_RANGE_4G:
            logging.warning(f'Acceleration range is set to {self.gyro.read_accel_range()}')
        self.gyro.set_gyro_range(gyro_range = self.gyro.GYRO_RANGE_250DEG)
        if self.gyro.read_gyro_range() != self.gyro.GYRO_RANGE_250DEG:
            logging.warning(f'Giroscope range is set to {self.gyro.read_gyro_range()}')
        self.gyro.set_filter_range(filter_range = self.gyro.FILTER_BW_10)
        try:
            self.cm = SHM()
        except:
            logging.error('No shared memory access')
        try:
            self.mqtt = MQTT_CLIENT(client_id = 'giroscopes', offline = offline)
        except:
            logging.error('No connection to MQTT broker')
    def read_data(self):
        accel_data = self.gyro.get_accel_data()
        gyro_data = self.gyro.get_gyro_data()
        timer = time.time()
        self.mqtt.send(topic = self.write_topic, event = f"acc_x,{timer},{accel_data['x']},bike/sensor/imu,double")
        self.mqtt.send(topic = self.write_topic, event = f"acc_y,{timer},{accel_data['y']},bike/sensor/imu,double")
        self.mqtt.send(topic = self.write_topic, event = f"acc_z,{timer},{accel_data['z']},bike/sensor/imu,double")
        self.mqtt.send(topic = self.write_topic, event = f"gyro_x,{timer},{gyro_data['x']},bike/sensor/imu,double")
        self.mqtt.send(topic = self.write_topic, event = f"gyro_y,{timer},{gyro_data['y']},bike/sensor/imu,double")
        self.mqtt.send(topic = self.write_topic, event = f"gyro_z,{timer},{gyro_data['z']},bike/sensor/imu,double")
       
if __name__ == "__main__":
    giro = GIROSCOPES(bus = 1)
    reader = READ_TRIGGER(2, giro.read_data)



