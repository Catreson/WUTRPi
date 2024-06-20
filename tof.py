from smbus2 import SMBus
import time
from common import MQTT_CLIENT, READ_TRIGGER
import logging
#I2C.require_repeated_start()

class TOF:
    def __init__(self, address: int = 0x21, busnum: int = 0) -> None:
        self.bus = SMBus(busnum)
        self.address = address
    def read(self)  -> str:
        data = self.bus.read_i2c_block_data(self.address, 0, 4)
        return f'{(data[0] << 8) + data[1]} {(data[2] << 8 + data[3])}'

class TOFs:
    
    write_topic = 'bike/sensor/tof'
      
    def __init__(self, tofs_in_use = [['rear_tof', 0x21]], busnum: int = 0, offline: int = 0) -> None:
        self.tofs_list  = []
        for tof in tofs_in_use:
            self.tofs_list.append([tof[0], TOF(tof[1], busnum)])
        try:
            self.mqtt = MQTT_CLIENT(client_id = 'pyrometers', offline = offline)
        except:
            logging.error('No connection to MQTT broker')
            
    def read_data(self) -> None:
        for tof in self.tofs_list:
            self.mqtt.send(topic = self.write_topic, event = f'{pyro[0]},{time.time() - self.mqtt.timestam},{pyro[1].readObject1()},bike/sensor/pyro,double')
        
if __name__ == "__main__":
    print("Please no use like that")
    tof = TOFs([['rear_tof', 0x21]], 1 ,0)
    reader = READ_TRIGGER(2, tof.read_data)
