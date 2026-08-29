import os
import sys
import time
import logging
import threading
import subprocess
from smbus2 import SMBus, i2c_msg
from common import MQTT_CLIENT, SHM, READ_TRIGGER

STR2STR_BIN = 'str2str'

# UBX-CFG-PRT: disable UART1 / UART2 / USB / SPI as an I/O port
DISABLE_UART1 = bytes([0xB5, 0x62, 0x06, 0x00, 0x14, 0x00, 0x01, 0x00, 0x00, 0x00, 0xD0, 0x08,
                        0x00, 0x00, 0x00, 0x96, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                        0x00, 0x00, 0x89, 0x46])
DISABLE_UART2 = bytes([0xB5, 0x62, 0x06, 0x00, 0x14, 0x00, 0x02, 0x00, 0x00, 0x00, 0xD0, 0x08,
                        0x00, 0x00, 0x00, 0x96, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                        0x00, 0x00, 0x8A, 0x5A])
DISABLE_SPI = bytes([0xB5, 0x62, 0x06, 0x00, 0x14, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x32,
                      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                      0x00, 0x00, 0x50, 0x86])

# UBX-CFG-RATE: measurement rate 1000ms, aligned to UTC/GPS/GAL/GLO/BDS time reference
SET_RATE_UTC = bytes([0xB5, 0x62, 0x06, 0x08, 0x06, 0x00, 0x19, 0x00, 0x01, 0x00, 0x00, 0x00, 0x2E, 0x4E])
SET_RATE_GPS = bytes([0xB5, 0x62, 0x06, 0x08, 0x06, 0x00, 0x19, 0x00, 0x01, 0x00, 0x01, 0x00, 0x2F, 0x50])
SET_RATE_GAL = bytes([0xB5, 0x62, 0x06, 0x08, 0x06, 0x00, 0x19, 0x00, 0x01, 0x00, 0x02, 0x00, 0x30, 0x52])
SET_RATE_GLO = bytes([0xB5, 0x62, 0x06, 0x08, 0x06, 0x00, 0x19, 0x00, 0x01, 0x00, 0x03, 0x00, 0x31, 0x54])
SET_RATE_BDS = bytes([0xB5, 0x62, 0x06, 0x08, 0x06, 0x00, 0x19, 0x00, 0x01, 0x00, 0x04, 0x00, 0x32, 0x56])

# UBX-CFG-VALSET: enable NMEA protocol out on I2C (DDC) and UART2
SET_NMEA = bytes([0xB5, 0x62, 0x06, 0x8A, 0x0E, 0x00, 0x00, 0x01, 0x00, 0x00, 0xAB, 0x00,
                   0x91, 0x20, 0x01, 0xB5, 0x00, 0x91, 0x20, 0x01, 0x63, 0x1C])

# UBX-CFG-VALSET: I2C output/input protocol selection
USB_SET = bytes([0xB5, 0x62, 0x06, 0x8A, 0x18, 0x00, 0x00, 0x01, 0x00, 0x00, 0x01, 0x00,
                  0x78, 0x10, 0x01, 0x01, 0x00, 0x78, 0x10, 0x01, 0x02, 0x00, 0x78, 0x10,
                  0x01, 0x01, 0x00, 0x77, 0x10, 0x01, 0xD1, 0x28, 0x00, 0x00])

# UBX-CFG-VALSET: enable GNRMC/GNGNS message output, disable the rest of the default NMEA set
GPS_EXC_SET = bytes([0xB5, 0x62, 0x06, 0x8A, 0x36, 0x00, 0x00, 0x01, 0x00, 0x00, 0x1F, 0x00,
                      0x31, 0x10, 0x01, 0x20, 0x00, 0x31, 0x10, 0x00, 0x01, 0x00, 0x31, 0x10,
                      0x01, 0x03, 0x00, 0x31, 0x10, 0x01, 0x04, 0x00, 0x31, 0x10, 0x01, 0x21,
                      0x00, 0x31, 0x10, 0x00, 0x22, 0x00, 0x31, 0x10, 0x00, 0x24, 0x00, 0x31,
                      0x10, 0x00, 0x25, 0x00, 0x31, 0x10, 0x00, 0x26, 0x00, 0x31, 0x10, 0x00,
                      0x4E, 0xA9])

UBX_COMMANDS = [
    DISABLE_UART1,
    DISABLE_UART2,
    DISABLE_SPI,
    SET_RATE_UTC,
    SET_RATE_GPS,
    SET_RATE_GAL,
    SET_RATE_GLO,
    SET_RATE_BDS,
    SET_NMEA,
    USB_SET,
    GPS_EXC_SET,
]

RTCM3_PREAMBLE = 0xD3
NO_DATA_BYTE = 0xFF


class GPS:

    write_topic = 'bike/sensor/gps'

    def __init__(self, busnum=1, address=0x42, offline=0, ntrip_url=None):
        self.address = address
        self.ntrip_url = ntrip_url if ntrip_url is not None else os.environ.get('NTRIP_URL')
        try:
            self.bus = SMBus(busnum)
        except FileNotFoundError:
            sys.exit(f'No I2C bus {busnum} available')
        self._send_config()

        try:
            self.cm = SHM()
        except Exception:
            logging.error('No shared memory access')

        try:
            self.mqtt = MQTT_CLIENT(client_id='gps', offline=offline)
        except Exception:
            sys.exit('No connection to MQTT broker')

        self.hdop = 0.0
        self.rtk_flag = 0
        self._nmea_buffer = bytearray()

    def _write_bytes(self, data):
        try:
            self.bus.i2c_rdwr(i2c_msg.write(self.address, data))
        except OSError as exc:
            logging.warning(f'GPS I2C write failed: {exc}')

    def _send_config(self):
        for command in UBX_COMMANDS:
            self._write_bytes(command)
            time.sleep(0.05)
        time.sleep(0.5)

    def _bytes_available(self):
        try:
            length_read = i2c_msg.read(self.address, 2)
            self.bus.i2c_rdwr(i2c_msg.write(self.address, [0xFD]), length_read)
            high, low = list(length_read)
        except OSError:
            return 0
        available = (high << 8) | low
        if available == 0xFFFF:
            return 0
        return available

    def _read_bytes(self, count):
        try:
            msg = i2c_msg.read(self.address, count)
            self.bus.i2c_rdwr(msg)
            return bytes(msg)
        except OSError as exc:
            logging.warning(f'GPS I2C read failed: {exc}')
            return b''

    @staticmethod
    def _dms_to_dd(value, hemisphere):
        if not value:
            raise ValueError('empty coordinate field')
        raw = float(value)
        degrees = int(raw / 100)
        minutes = raw - degrees * 100
        dd = degrees + minutes / 60
        if hemisphere in ('S', 'W'):
            dd = -dd
        return dd

    @staticmethod
    def _checksum_ok(body, checksum_hex):
        try:
            expected = int(checksum_hex, 16)
        except ValueError:
            return False
        calc = 0
        for ch in body:
            calc ^= ord(ch)
        return calc == expected

    def _handle_rmc(self, fields):
        if len(fields) < 9 or fields[2] != 'A':
            return
        try:
            lat = self._dms_to_dd(fields[3], fields[4])
            lon = self._dms_to_dd(fields[5], fields[6])
            speed_kmh = 1.852 * float(fields[7]) if fields[7] else 0.0
            course = fields[8] if fields[8] else '0'
        except (ValueError, IndexError):
            return
        stamp = time.time() - self.mqtt.timestam
        event = f'gps,{stamp},{lon} {lat} {speed_kmh} {course} {self.hdop} {self.rtk_flag},bike/sensor/gps,string'
        self.mqtt.send(topic=self.write_topic, event=event)
        self.cm.save('gps_lat', lat)
        self.cm.save('gps_lon', lon)
        self.cm.save('gps_speed', speed_kmh)
        try:
            self.cm.save('gps_course', float(course))
        except ValueError:
            pass

    def _handle_gns(self, fields):
        if len(fields) < 9:
            return
        mode = fields[6]
        hdop_field = fields[8]
        if not mode or not hdop_field:
            self.hdop = 0.0
            return
        try:
            self.hdop = float(hdop_field)
        except ValueError:
            self.hdop = 0.0
        self.rtk_flag = 1 if 'R' in mode else 0
        self.cm.save('gps_hdop', self.hdop)
        self.cm.save('gps_rtk', self.rtk_flag)
        self.cm.save('rtk_flag', self.rtk_flag)
        try:
            self.cm.save('gps_sats', int(fields[7]))
        except (ValueError, IndexError):
            pass

    def _handle_sentence(self, raw):
        try:
            line = raw.decode('ascii', errors='ignore').strip()
        except UnicodeDecodeError:
            return
        if not line.startswith('$') or '*' not in line:
            return
        body, _, checksum = line[1:].partition('*')
        if not self._checksum_ok(body, checksum):
            return
        fields = body.split(',')
        talker = fields[0]
        if talker.endswith('RMC'):
            self._handle_rmc(fields)
        elif talker.endswith('GNS'):
            self._handle_gns(fields)

    def read_nmea_loop(self):
        while True:
            available = self._bytes_available()
            if available == 0:
                time.sleep(0.05)
                continue
            chunk = self._read_bytes(min(available, 256))
            for byte in chunk:
                if byte == NO_DATA_BYTE:
                    continue
                if byte == 0x0D:
                    continue
                if byte == 0x0A:
                    if self._nmea_buffer:
                        self._handle_sentence(bytes(self._nmea_buffer))
                        self._nmea_buffer.clear()
                else:
                    self._nmea_buffer.append(byte)
                    if len(self._nmea_buffer) > 200:
                        self._nmea_buffer.clear()

    def _start_str2str(self):
        try:
            return subprocess.Popen([STR2STR_BIN, '-in', self.ntrip_url], stdout=subprocess.PIPE)
        except OSError as exc:
            logging.error(f'Failed to start str2str: {exc}')
            return None

    def forward_rtcm_loop(self):
        if not self.ntrip_url:
            logging.warning('NTRIP_URL not set, GPS will run without RTCM corrections')
            return
        while True:
            proc = self._start_str2str()
            if proc is None:
                time.sleep(5)
                continue
            stream = proc.stdout
            while True:
                if proc.poll() is not None:
                    logging.warning('str2str exited unexpectedly, restarting it')
                    break
                preamble = stream.read(1)
                if not preamble:
                    time.sleep(0.1)
                    continue
                if preamble[0] != RTCM3_PREAMBLE:
                    continue
                header = stream.read(2)
                if len(header) < 2:
                    continue
                length = ((header[0] & 0x03) << 8) | header[1]
                payload = stream.read(length)
                crc = stream.read(3)
                if len(payload) < length or len(crc) < 3:
                    logging.warning('Incomplete RTCM3 frame, dropping')
                    continue
                self._write_bytes(preamble + header + payload + crc)
            time.sleep(2)

    def run(self):
        rtcm_thread = threading.Thread(target=self.forward_rtcm_loop, daemon=True)
        rtcm_thread.start()
        self.read_nmea_loop()


if __name__ == "__main__":
    print("Please no use like that")
    gps = GPS()
    gps.run()
