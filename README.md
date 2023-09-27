# WUTRPi
![image](https://wsrt.pl/wp-content/uploads/2023/01/wut_simr_racing_technology-2048x828.png)

Software for RPi 4B used in WUT SiMR Racing Technology racing motorcycle. \
Project is run on Warsaw University of Technology, SiMR faculty. 

Find us:\
http://wsrt.pl \
[Facebook](https://www.facebook.com/wutsimracing/) \
[Instagram](https://www.instagram.com/wutsimracingtech/)

# Modules description
common - shared classes\
main - used to run and maintain modules' lifes\
gyro - used to run MPU6050 accelerometer + gyroscope (IMU), communication through SMBus\
pyro - used to run multiple MLX90614 pyrometers through SMBus\
susp - used to run ADS1263 analog readings from linear potentiometers (suspension_front, suspension_read, steer_angle) and brake pressure sensor, communication through SPI\
rs232 - used to capture data from ECUMaster EMU Black, transfered by AIM dash protocol\
mqtt_gps - used to pass RTCM ntrip stream to gps module and read GNSS data, made from [Matusz's](https://github.com/mklisiewicz/WSRT/tree/main/PiProjects/GNSS). Has to receive ntrip stream via str2str from RTKlib. Communication through I2C   \
backup - used to backup esp output data exposed to overwrite when rebooting \
leds - managing LED strip, gear display and ECU mode

# Hardware description
Raspberry Pi 4B 4GB\
4.3 inch touch display\
ADS1263 ADC HAT from WaveShare\
3 linear potentiometers\
Bosch 0265 005 303 brake pressure sensor\
6 MLX90614 pytometers\
2 MPU6050 accelerometers + gyroscopes\
SparkFun GPS-RTK-SMA Breakout - ZED-F9P\
SIM7600E-H 4G HAT\
2 wheel speed sensors from Yamaha R3\
RP2040 used to manage speed sensors\
Motorcycle

# Software list:
Software listed in modules description\
Mosquitto MQTT broker\
SAS ESP from our sponsor SAS Institute\
Speed sensors software by [Mateusz Klisiewicz](https://github.com/mklisiewicz/WSRT/tree/main/PiProjects/SpeedSensor)

![image](https://drive.google.com/uc?export=view&id=13yYR1pqgYXPpYR2iEUEK7wSMa94LrRi7)



