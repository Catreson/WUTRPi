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
mqtt_gps - used to pass RTCM ntrip stream to gps module and read GNSS data \
backup - used to backup esp output data exposed to overwrite when rebooting \
leds - managing LED strip, gear display and ECU mode \
disp4 - interactive GUI to work with 4.3 inch touchscreen

![image](https://drive.google.com/uc?export=view&id=1jlI3O5ybrKBeGud8adDAkh9nt0LPHp7L)

# Hardware description
Raspberry Pi 4B 4GB\
4.3 inch touch display\
ADS1263 ADC HAT from WaveShare\
3 linear potentiometers\
Bosch 0265 005 303 brake pressure sensor\
6 MLX90614 pyrometers\
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

# Running
`main.py` is the single entry point: it starts every module (ecu, susp, giro, pyro, gps, leds, display) as a supervised child process and restarts any of them that crash. `rc.local` (or whatever starts the software on boot) should launch only:

```
NTRIP_URL="ntrip://user:pass@host:port/mountpoint" python3 /home/catreson/WUTRPi/main.py
```

`gps.py` (`gps_proc`) starts and supervises `str2str` itself using `NTRIP_URL`, restarting it if the connection drops. `main.py` will still start and run every other module fine without `NTRIP_URL` set.

`/etc/rc.local` on the Pi is generated from [deploy/rc.local.template](deploy/rc.local.template), which keeps the real ntrip password out of git. To (re)install it on the Pi:
```
cd /home/catreson/WUTRPi/deploy
cp ntrip_credentials.sh.example ntrip_credentials.sh   # first time only, then fill in your ASG-EUPOS account
sudo ./install_rc_local.sh
```
`ntrip_credentials.sh` is gitignored - never commit it. If you change anything else in `rc.local`, edit `rc.local.template` and re-run the install script rather than editing `/etc/rc.local` directly, so the change stays tracked.

# Log export (Google Drive)
The touchscreen's EXPORT screen runs `rclone copy /home/catreson/dane_esp_write/ gdrive2:WUTRPi-logs` (in [disp4.py](disp4.py)) - it only uploads new/changed files, never deletes anything on the Drive side, so it's safe to press repeatedly. The remote is named `gdrive2` (not `gdrive`) because the Pi already had an older, unrelated `gdrive` rclone remote configured - reusing that name would have repointed/overwritten it. `rclone` needs a one-time setup on the Pi that can't be done from the touchscreen, since it requires a browser to authorize with Google:

1. Install rclone: `curl https://rclone.org/install.sh | sudo bash`
2. On a machine with a browser (doesn't have to be the Pi), run `rclone authorize "drive"` and follow the link to sign in with the Google account you want logs uploaded to. It prints a config token when done.
3. On the Pi, run `rclone config`, create a new remote named exactly `gdrive2`, type `drive`, and when it asks about auto config say no and paste the token from step 2 instead.
4. Test it once by hand: `rclone copy /home/catreson/dane_esp_write/ gdrive2:WUTRPi-logs --progress`

After that one-time setup, the EXPORT button just works.

![image](https://drive.google.com/uc?export=view&id=13yYR1pqgYXPpYR2iEUEK7wSMa94LrRi7)



