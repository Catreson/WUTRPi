import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from zipfile import ZipFile
import time
def sort_meth(e):
    return e[1]

gauth = GoogleAuth()
drive = GoogleDrive(gauth)
pather = '/home/catreson/dane_esp_write/'

entries = os.listdir(pather)
nams = []

for filnam in entries:
    try:
        if 'gps' in filnam:
            nam = filnam.split('.')
            stamp = nam[0].split('_')
            att = stamp[2]
            nams.append([int(stamp[2]), nam[0]])
    except:
        print('err')
nams.sort(key=sort_meth,reverse=True)
target = f'{pather}{nams[0][1]}.csv'
with ZipFile(f'{nams[0][1]}.zip', 'w') as zip_object:
    zip_object.write(target)

target = f'{nams[0][1]}.zip'

gfile = drive.CreateFile({'parents': [{'id': '1mHOWBAdyFfs5vespprBn5V26pFZ0ljEo'}]})
gfile.SetContentFile(target)

is_uploaded = False

while not is_uploaded:
    gfile.Upload()
    is_uploaded = gfile.uploaded
    time.sleep(5)