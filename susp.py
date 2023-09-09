import sys
import time
import logging
from lib import ADS1263
from common import MQTT_CLIENT, SHM, READ_TRIGGER


class SUSPENSION():
    ANALOG_RANGE = 0x7fffffff
    corr_f = 0
    corr_r = 0
    corr_sa = 0
    corr_pb = 0
    corr_dict = {'susp_f': corr_f, 'susp_r': corr_r, 'p_brake': corr_pb, 'steer_angle': corr_sa}
    channelList = [0, 1, 2, 3]
    val = [0] * 4
    write_topic = 'bike/sensor/susp/'
    listen_topic = 'bike/correction/susp'

    def correction(self, client, userdata, message):
        mesenge = str(message.payload.decode("utf-8"))
        print("message received ", mesenge)
        print("message topic=", message.topic)
        print(mesenge)
        if message.topic == 'bike/correction/susp':
            try:
                if 'susp_f' in mesenge:
                    self.corr_f = self.val[0]
                elif 'susp_r' in mesenge:
                    self.corr_r = self.val[1] - self.ANALOG_RANGE
                elif 'p_brake' in mesenge:
                    self.corr_pb = self.val[2]
                elif 'steer_angle' in mesenge:
                    self.corr_sa = self.val[3]
            except:
                print('err')
            with open("/home/catreson/WUTRPi/res/correction.csv", "w") as file:
                for kej in self.corr_dict.keys():
                    print(f'{kej},{self.corr_dict[kej]}\n')
                    file.write(f'{kej},{self.corr_dict[kej]}\n')
        logging.info('Received correction message')

    def __init__(self, offline=0):

        logging.info('Init susp')
        self.ADC = ADS1263.ADS1263()
        if self.ADC.ADS1263_init_ADC1('ADS1263_19200SPS') == -1:
            sys.exit('ADC failed to initialize')
        self.ADC.ADS1263_SetMode(0)  # 0 is singleChannel, 1 is diffChannel
        logging.info('ADC set')

        try:
            self.cm = SHM()
        except:
            sys.exit('No shared memory access')
        logging.info('SHM set')

        logging.info('Creating client')
        try:
            print('MQTT init')
            self.mqtit = MQTT_CLIENT(client_id='suspension', offline=offline)
            print('MQTT created')
            logging.info('Created client')
            self.mqtit.subscribe(self.listen_topic, self.correction)
            print('MQTT set')
            logging.info('Client connected')
        except:
            sys.exit('No connection to MQTT broker')
        with open("/home/catreson/WUTRPi/res/correction.csv", "r") as file:
            for line in file:
                line = line.strip()
                dat = line.split(',')
                self.corr_dict[dat[0]] = float(dat[1])

    def ch_shock(self, potentiometer_length):
        return 0.0030 * pow(potentiometer_length, 2) - 1.6297 * potentiometer_length + 105.3946
    def ch_steer(self, potentiometer_length):
        return -0.0006 * pow(potentiometer_length, 2) - 0.4231 * potentiometer_length + -0.0026
    def potentiometer(self, analog_value, potentiometer_length):
        return potentiometer_length * analog_value / self.ANALOG_RANGE

    def read_data(self):
        self.val = self.ADC.ADS1263_GetAll(self.channelList)
        print(self.val)
        susp_f = self.potentiometer(analog_value=(self.val[0] - self.corr_f), potentiometer_length=150)
        pot_r = self.potentiometer(analog_value=(self.val[1] - self.corr_r), potentiometer_length=75)
        susp_r = self.ch_shock(pot_r)
        p_brake = self.potentiometer(analog_value=self.val[2] - self.corr_pb, potentiometer_length=227)
        pot_sa = self.potentiometer(analog_value=self.val[3] - self.corr_sa, potentiometer_length=150)
        steer_angle = self.ch_steer(pot_sa)
        self.cm.save('susp_f', susp_f)
        self.cm.save('susp_r', susp_r)
        self.cm.save('p_brake', p_brake)
        self.cm.save('steer_angle', steer_angle)
        even = f'susp,{time.time()},{susp_f} {susp_r} {p_brake} {steer_angle},bike/sensor/susp,string'
        self.mqtit.send(topic=self.write_topic, event=even)

    def __del__(self):
        print("Program end")
        self.ADC.ADS1263_Exit()


if __name__ == "__main__":
    susp = SUSPENSION(offline=1)
    trigger = READ_TRIGGER(0.005, susp.read_data)
