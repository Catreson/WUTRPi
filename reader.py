from common import SHM, MQTT_CLIENT
import time
shm = SHM()
mqtit = MQTT_CLIENT(client_id = 'reader', offline = 0)
ptime = 0.0
ptim = 0.0
tim = 0.0
i = 0
while True:
    i += 1
    print(f'Loop {i}')
    with open('/home/catreson/WUTRPi/gps_reader.csv', 'r') as file:
        pline = file.readline()
        pline = pline.strip()
        for line in file:
            line = line.strip()
            lin = line.split(',')
            #print(line)
            try:
                tim = float(lin[1])
            except:
                print('Invalid')
            mqtit.send(topic = lin[3], event = f'lin[0],{float(lin[1]) + ptime},lin[2],lin[3],lin[4]')
            try:
                if 'susp' in lin[0]:
                    sup = lin[2].split(' ')
                    #print(f'susp_f, sup[0]')
                    shm.save('susp_f', float(sup[0]))
                    #print(f'susp_f {float(sup[0])}')
                    shm.save('susp_r', float(sup[1]))
                    shm.save('steer_angle', float(sup[2]))
                    shm.save('p_brake', float(sup[3]))

                else:
                    shm.save(lin[0], float(lin[2]))
            except:
                pass
            diff = tim - ptim
            ptim = tim
            time.sleep(abs(diff) if abs(diff) < 1 else 1)
        ptime = ptim
