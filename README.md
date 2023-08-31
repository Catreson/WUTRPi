# WUTRPi
Scripts for RPi used in WUT SiMR Racing Technology racing motorcycle, project is run on Warsaw University of Technology, SiMR faculty.
Everything is prepared to work with SAS ESP, passing data by Mosquitto MQTT broker.

Module name description:
common - common stuff\
main - used to run and maintain modules' lifes\
gyro - used to run MPU6050 accelerometer + gyroscope (IMU)\
pyro - used to run multiple MLX90614 pyrometers\
susp - used to run ADS1263 analog readings from linear potentiometers (suspension_front, suspension_read, steer_angle) and brake pressure sensor\
rs232 - used to capture data from ECUMaster EMU Black, transfered by AIM dash protocol\
gps - used to launch program managing GPS(written by Mateusz Klisiewicz)\
backup - used to backup data exposed to overwrite when reboot\

