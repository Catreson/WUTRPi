import csv
import time
from common import SHM, READ_TRIGGER


class LOGGER:

    write_path = '/home/catreson/dane_esp_write/'

    def __init__(self):
        self.cm = SHM()
        columns = sorted(self.cm.names_dict.items(), key=lambda kv: kv[1])
        self.columns = [name for name, idx in columns]
        filename = f'{self.write_path}log_{round(time.time())}.csv'
        self.file = open(filename, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['timestamp'] + self.columns)
        self.file.flush()

    def log_row(self):
        data = self.cm.read_bulk()
        self.writer.writerow([time.time()] + list(data))
        self.file.flush()


if __name__ == "__main__":
    logger = LOGGER()
    trigger = READ_TRIGGER(frequency=200, func=logger.log_row)
