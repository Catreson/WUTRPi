import shutil
import time
import logging

czas = time.strftime("%Y%m%d%H%M%S")
try:
    shutil.copy2('/home/catreson/dane_esp_write/output_stream.csv', '/home/catreson/dane_esp_write/output_stream' + czas + '.csv')
    logging.info('Made backup')
except:
    logging.warning('Backup impossible')

