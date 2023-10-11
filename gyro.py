import time
from mpu6050 import mpu6050
import logging
from common import MQTT_CLIENT, SHM, READ_TRIGGER


class GIROSCOPES:

    address = 0x68   
    write_topic = 'bike/sensor/imu'
    gyro_list = []
    eventlist = ""
    index = 0
    def __init__(self, address = [0x68], bus = 1, offline = 0):

        for gyro_address in address:
            try:
                gyro = mpu6050(gyro_address, bus)
                gyro.set_accel_range(accel_range = gyro.ACCEL_RANGE_4G)
                if gyro.read_accel_range() != gyro.ACCEL_RANGE_4G:
                    logging.warning(f'Acceleration range is set to {gyro.read_accel_range()}')
                gyro.set_gyro_range(gyro_range = gyro.GYRO_RANGE_250DEG)
                if gyro.read_gyro_range() != gyro.GYRO_RANGE_250DEG:
                    logging.warning(f'Giroscope range is set to {gyro.read_gyro_range()}')
                gyro.set_filter_range(filter_range = gyro.FILTER_BW_10)
            except:
                print(f"Err setup {gyro_address}")
            else:
                self.gyro_list.append(gyro)
        try:
            self.cm = SHM()
        except:
            logging.error('No shared memory access')
        try:
            self.mqtt = MQTT_CLIENT(client_id = 'giroscopes', offline = offline)
        except:
            logging.error('No connection to MQTT broker')
    def read_data(self):
        i = 1
        for gyro in self.gyro_list:
            """try:
                accel1_data = gyro.get_accel_data(g = True)
                gyro1_data = gyro.get_gyro_data()
                self.mqtt.send(topic=self.write_topic,
                       event=f"gyro{i},{time.time() - self.mqtt.timestam},{accel1_data['x']} {accel1_data['y']} {accel1_data['z']} {gyro1_data['x']} {gyro1_data['y']} {gyro1_data['z']},bike/sensor/imu,double")
            except:
                print("err1")
            finally:
                i += 1
            """
            try:
                accel1_data = gyro.get_accel_data(g = True)
                gyro1_data = gyro.get_gyro_data()
                self.eventlist += f"gyro{i};{time.time() - self.mqtt.timestam};{accel1_data['x']};{accel1_data['y']};{accel1_data['z']};{gyro1_data['x']};{gyro1_data['y']};{gyro1_data['z']}:"
            except:
                print("err1")
            finally:
                i += 1

        self.index += 1
        if self.index >= 10:
            self.mqtt.send(topic=self.write_topic,
                           event=f"gyro{i},{time.time() - self.mqtt.timestam},{self.eventlist},bike/sensor/imu,double")
            self.eventlist = ""
            self.index = 0



if __name__ == "__main__":
    giro = GIROSCOPES(bus = 1)
    reader = READ_TRIGGER(2, giro.read_data)
