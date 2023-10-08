import time
from mpu6050 import mpu6050
import logging
from common import MQTT_CLIENT, SHM, READ_TRIGGER


class GIROSCOPES:

    address = 0x68   
    write_topic = 'bike/sensor/imu'
    
    def __init__(self, address = 0x68, bus = 1, offline = 0):
        self.gyro1 = mpu6050(address, bus)
        self.gyro1.set_accel_range(accel_range = self.gyro1.ACCEL_RANGE_4G)
        if self.gyro1.read_accel_range() != self.gyro1.ACCEL_RANGE_4G:
            logging.warning(f'Acceleration range is set to {self.gyro1.read_accel_range()}')
        self.gyro1.set_gyro_range(gyro_range = self.gyro1.GYRO_RANGE_250DEG)
        if self.gyro1.read_gyro_range() != self.gyro1.GYRO_RANGE_250DEG:
            logging.warning(f'Giroscope range is set to {self.gyro1.read_gyro_range()}')
        self.gyro1.set_filter_range(filter_range = self.gyro1.FILTER_BW_10)

        self.gyro2 = mpu6050(0x69, bus)
        self.gyro2.set_accel_range(accel_range=self.gyro2.ACCEL_RANGE_4G)
        if self.gyro2.read_accel_range() != self.gyro2.ACCEL_RANGE_4G:
            logging.warning(f'Acceleration range is set to {self.gyro2.read_accel_range()}')
        self.gyro2.set_gyro_range(gyro_range=self.gyro2.GYRO_RANGE_250DEG)
        if self.gyro2.read_gyro_range() != self.gyro2.GYRO_RANGE_250DEG:
            logging.warning(f'Giroscope range is set to {self.gyro2.read_gyro_range()}')
        self.gyro2.set_filter_range(filter_range=self.gyro2.FILTER_BW_10)
        try:
            self.cm = SHM()
        except:
            logging.error('No shared memory access')
        try:
            self.mqtt = MQTT_CLIENT(client_id = 'giroscopes', offline = offline)
        except:
            logging.error('No connection to MQTT broker')
    def read_data(self):
        accel1_data = self.gyro1.get_accel_data()
        gyro1_data = self.gyro1.get_gyro_data()
        accel2_data = self.gyro2.get_accel_data()
        gyro2_data = self.gyro2.get_gyro_data()
        """
        self.mqtt.send(topic = self.write_topic, event = f"acc_x,{time.time() - self.mqtt.timestam},{accel_data['x']},bike/sensor/imu,double")
        self.mqtt.send(topic = self.write_topic, event = f"acc_y,{time.time() - self.mqtt.timestam},{accel_data['y']},bike/sensor/imu,double")
        self.mqtt.send(topic = self.write_topic, event = f"acc_z,{time.time() - self.mqtt.timestam},{accel_data['z']},bike/sensor/imu,double")
        self.mqtt.send(topic = self.write_topic, event = f"gyro_x,{time.time() - self.mqtt.timestam},{gyro_data['x']},bike/sensor/imu,double")
        self.mqtt.send(topic = self.write_topic, event = f"gyro_y,{time.time() - self.mqtt.timestam},{gyro_data['y']},bike/sensor/imu,double")
        self.mqtt.send(topic = self.write_topic, event = f"gyro_z,{time.time() - self.mqtt.timestam},{gyro_data['z']},bike/sensor/imu,double")
        """
        self.mqtt.send(topic=self.write_topic,
                       event=f"gyro1,{time.time() - self.mqtt.timestam},{accel1_data['x']} {accel1_data['y']} {accel1_data['z']} {gyro1_data['x']} {gyro1_data['y']} {gyro1_data['z']},bike/sensor/imu,double")
        self.mqtt.send(topic=self.write_topic,
                       event=f"gyro2,{time.time() - self.mqtt.timestam},{accel2_data['x']} {accel2_data['y']} {accel2_data['z']} {gyro2_data['x']} {gyro2_data['y']} {gyro2_data['z']},bike/sensor/imu,double")
if __name__ == "__main__":
    giro = GIROSCOPES(bus = 1)
    reader = READ_TRIGGER(2, giro.read_data)



