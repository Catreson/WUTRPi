import signal
import subprocess
import time
import logging

ARCHIVE_DIR = '/home/catreson/dane_esp_write/'
TOPIC = 'bike/sensor/#'


def run_mqtt_archive():
    """Raw MQTT sensor traffic archive, previously a bare `mosquitto_sub` line in
    rc.local. Brought under process supervision so it can be paused/resumed the same
    way as logger_proc (e.g. while exporting, or via the touchscreen PROCESSES screen)."""
    current = {'proc': None}

    def _handle_term(signum, frame):
        if current['proc'] is not None:
            current['proc'].terminate()
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _handle_term)

    while True:
        filename = f'{ARCHIVE_DIR}rad_gps_input_{time.strftime("%Y%m%d%H%M%S", time.gmtime())}.csv'
        try:
            with open(filename, 'w') as f:
                proc = subprocess.Popen(['mosquitto_sub', '-t', TOPIC], stdout=f, stderr=subprocess.STDOUT)
                current['proc'] = proc
                proc.wait()
            logging.warning('mqtt_archive: mosquitto_sub exited, restarting')
        except OSError as exc:
            logging.warning(f'mqtt_archive failed: {exc}')
        time.sleep(2)


if __name__ == "__main__":
    run_mqtt_archive()
