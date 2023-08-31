import Adafruit_GPIO.I2C as I2C
import time
from .lib.common import MQTT_CLIENT, READ_TRIGGER
import logging
#I2C.require_repeated_start()
import io


class Melexis:

    def __init__(self, address, busnum = 0):
        self._i2c = I2C.Device(address, busnum)

    def readAmbient(self):
        return self._readTemp(0x06)

    def readObject1(self):
        return self._readTemp(0x07)

    def readObject2(self):
        return self._readTemp(0x08)

    def _readTemp(self, reg):
        temp = self._i2c.readS16(reg)
        temp = temp * .02 - 273.15
        return temp

class PYROMETERS:
    
    write_topic = 'bike/sensor/pyro'
    pyro_list = []
      
    def __init__(self, pyrometers_in_use = [['pyro_rc', 0x5a],['pyro_rr', 0x6a],['pyro_rl', 0x7a]], busnum = 0, offline = 0):
        for pyrometer in pyrometers_in_use:
            self.pyro_list.append([pyrometer[0], Melexis(pyrometer[1], busnum = busnum)])
        try:
            self.mqtt = MQTT_CLIENT(client_id = 'pyrometers', offline = offline)
        except:
            logging.error('No connection to MQTT broker')
            
    def read_data(self):
        for pyro in self.pyro_list:
            self.mqtt.send(topic = self.write_topic, event = f'{pyro[0]},{time.time()},{pyro[1].readObject1()},bike/sensor/pyro,double')
        
if __name__ == "__main__":
    print("Please no use like that")
    pyro = PYROMETERS()
    reader = READ_TRIGGER(2, pyro.read_data)
