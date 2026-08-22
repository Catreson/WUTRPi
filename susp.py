import sys
import time
import logging
from lib import ADS1263
from common import MQTT_CLIENT, SHM, READ_TRIGGER

CORRECTION_CHANNELS = {1: 'susp_f', 2: 'susp_r', 3: 'p_brake', 4: 'steer_angle'}


class SUSPENSION():
    ANALOG_RANGE = 0x7fffffff
    channelList = [0, 1, 2, 3]
    write_topic = 'bike/sensor/susp/'

    def apply_correction(self, request_code):
        channel_name = CORRECTION_CHANNELS.get(request_code)
        if channel_name is None:
            return
        try:
            if channel_name == 'susp_f':
                self.corr_dict['susp_f'] = self.val[0]
            elif channel_name == 'susp_r':
                self.corr_dict['susp_r'] = self.val[1] - self.ANALOG_RANGE
            elif channel_name == 'p_brake':
                self.corr_dict['p_brake'] = self.val[2]
            elif channel_name == 'steer_angle':
                self.corr_dict['steer_angle'] = self.val[3]
        except Exception as exc:
            logging.warning(f'Correction apply failed for {channel_name}: {exc}')
            return
        try:
            with open("/home/catreson/WUTRPi/res/correction.csv", "w") as file:
                for kej in self.corr_dict.keys():
                    file.write(f'{kej},{self.corr_dict[kej]}\n')
        except OSError as exc:
            logging.warning(f'Failed to write correction.csv: {exc}')
        logging.info(f'Applied correction for {channel_name}')

    def __init__(self, offline=0):
        self.corr_dict = {}
        self.val = [0] * 4
        self.eventlist = ""
        self.index = 0

        logging.info('Init susp')
        self.ADC = ADS1263.ADS1263()
        if self.ADC.ADS1263_init_ADC1('ADS1263_7200SPS') == -1:
            sys.exit('ADC failed to initialize')
        self.ADC.ADS1263_SetMode(0)  # 0 is singleChannel, 1 is diffChannel
        logging.info('ADC set')

        try:
            self.cm = SHM()
        except:
            sys.exit('No shared memory access')
        logging.info('SHM set')
        self.cm.save('susp_correction_request', 0)

        logging.info('Creating client')
        try:
            print('MQTT init')
            self.mqtit = MQTT_CLIENT(client_id='suspension', offline=offline)
            print('MQTT created')
            logging.info('Created client')
        except:
            sys.exit('No connection to MQTT broker')
        try:
            with open("/home/catreson/WUTRPi/res/correction.csv", "r") as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    dat = line.split(',')
                    if len(dat) < 2:
                        continue
                    self.corr_dict[dat[0]] = float(dat[1])
        except FileNotFoundError:
            logging.warning('No correction.csv found, starting with empty corrections')

    def ch_shock(self, potentiometer_length):
        return 0.0030 * pow(potentiometer_length, 2) - 1.6297 * potentiometer_length + 105.3946
    def ch_steer(self, potentiometer_length):
        return -0.0006 * pow(potentiometer_length, 2) - 0.4231 * potentiometer_length + -0.0026

    def potentiometer(self, analog_value, potentiometer_length):
        return potentiometer_length * analog_value / self.ANALOG_RANGE

    def read_data(self):
        self.val = self.ADC.ADS1263_GetAll(self.channelList)

        request = int(self.cm.read('susp_correction_request'))
        if request != 0:
            self.apply_correction(request)
            self.cm.save('susp_correction_request', 0)

        susp_f = self.potentiometer(analog_value=(self.val[0] - self.corr_dict.get('susp_f', 0)), potentiometer_length=150)
        pot_r = self.potentiometer(analog_value=(self.val[1] - self.corr_dict.get('susp_r', 0)), potentiometer_length=75)
        susp_r = self.ch_shock(pot_r)
        p_brake = self.potentiometer(analog_value=self.val[2] - self.corr_dict.get('p_brake', 0), potentiometer_length=227)
        pot_sa = self.potentiometer(analog_value=self.val[3] - self.corr_dict.get('steer_angle', 0), potentiometer_length=150)
        steer_angle = self.ch_steer(pot_sa)


        self.cm.save('susp_f', susp_f)
        self.cm.save('susp_r', susp_r)
        self.cm.save('p_brake', p_brake)
        self.cm.save('steer_angle', steer_angle)
        even = f'susp,{time.time() - self.mqtit.timestam},{susp_f} {susp_r} {p_brake} {steer_angle},bike/sensor/susp,string'
        self.mqtit.send(topic=self.write_topic, event=even)

    def __del__(self):
        print("Program end")
        self.ADC.ADS1263_Exit()


if __name__ == "__main__":
    susp = SUSPENSION(offline=1)
    trigger = READ_TRIGGER(1, susp.read_data)
