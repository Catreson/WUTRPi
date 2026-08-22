import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from zipfile import ZipFile
import time
import sys
import time
import pandas as pd
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

filnam = target.split('.')
file = open(target, 'r')
nam = f'{filnam[0]}ek.csv'
ilef = open(nam, 'w')

prevline = file.readline()
prevlin = prevline.split(',')
timdfrift = 0
for line in file:
    lin = line.split(',')
    if lin[0] == 'gps' and prevlin[0] != 'gps':
        timdrift = round(float(prevlin[1]) - float(lin[1]))
        print(timdrift)
        break
    prevlin = lin
file.close()

file = open(target, 'r')
prevline = file.readline()
for line in file:
    lin = line.split(',')
    if lin[0] == 'gps':
        try:
            pom = lin[2].split(' ')
            lat = pom[0]
            lon = pom[1]
            ilef.write(
                f'gps,{float(lin[1]) + timdrift},{lat} {lon} {pom[2]} {pom[3]} {pom[4]} {pom[5]},bike/sensor/gps,string\n')
        except:
            try:
                pom = lin[2].split(' ')
                lat = pom[0]
                lon = pom[1]
                ilef.write(f'gps,{float(lin[1]) + timdrift},{lat} {lon} {pom[2]} {pom[3]},bike/sensor/gps,string\n')

            except:
                print('Err')
    else:
        ilef.write(line)
print('Done')
ilef.close()
file.close()
df_csv = pd.read_csv(nam, names = ['tag', 'timestamp', 'value', 'topic', 'datatype'] )
df_csv.sort_values("timestamp", axis=0, ascending=True,inplace=True, na_position='first')
df_csv.to_csv(nam, index=False)
file = open(nam, 'r')
ilef = open(f'{filnam[0]}e.csv', 'w')
err = 0
for i in range(5):
    dumper = file.readline()
for line in file:
    lin = line.split(',')
    if lin[0] != 'err':
        ilef.write(line)
file.close()
ilef.close()
with ZipFile(f'{nams[0][1]}.zip', 'w') as zip_object:
    zip_object.write(target)
    zip_object.write(f'{filnam[0]}e.csv')
target = f'{nams[0][1]}.zip'

gfile = drive.CreateFile({'parents': [{'id': '1mHOWBAdyFfs5vespprBn5V26pFZ0ljEo'}]})
gfile.SetContentFile(target)

is_uploaded = False

while not is_uploaded:
    gfile.Upload()
    is_uploaded = gfile.uploaded
    time.sleep(5)