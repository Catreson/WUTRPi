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
The touchscreen's EXPORT screen runs `rclone copy /home/catreson/dane_esp_write/ gdrive2:WUTRPi-logs` (in [disp4.py](disp4.py)) - it only uploads new/changed files, never deletes anything on the Drive side, so it's safe to press repeatedly. The remote is named `gdrive2` (not `gdrive`) because the Pi already had an older, unrelated `gdrive` rclone remote configured - reusing that name would have repointed/overwritten it.

`rclone` needs a one-time setup that authorizes it against your Google account. The Pi is headless (no browser), so **do not** try to run the whole setup on the Pi - the "Use auto config?" step in `rclone config` will try to open a browser (or a localhost URL) *on the Pi itself*, which is unreachable and just hangs/fails. The reliable way around this is to do the entire setup on your laptop (which has a real browser) and then copy the resulting config over to the Pi.

**On your laptop:**
1. Install rclone: https://rclone.org/downloads/ (or `sudo apt install rclone` / `brew install rclone`, on Windows download the zip).
2. Run `rclone config`. Answer the prompts:
   - `e/n/d/r/c/s/q>` → `n` (new remote)
   - `name>` → `gdrive2`
   - `Storage>` → type `drive` (or the number next to "Google Drive" in the list)
   - `client_id>` → leave blank, press enter
   - `client_secret>` → leave blank, press enter
   - `scope>` → `1` (full access)
   - `root_folder_id>` → leave blank, press enter
   - `service_account_file>` → leave blank, press enter
   - `Edit advanced config?` → `n`
   - `Use auto config?` → **`y`** (fine here - this machine has a browser)
   - A browser tab opens - sign in with the Google account you want logs uploaded to, click Allow.
   - `Configure this as a Shared Drive?` → `n`
   - `y/e/d>` → `y` to keep it
   - `q` to quit config
3. Find the config file rclone just wrote: `rclone config file` (prints the exact path - e.g. `~/.config/rclone/rclone.conf` on Linux/Mac, `%APPDATA%\rclone\rclone.conf` on Windows). Open it and copy the whole `[gdrive2]` section (a few lines starting with `[gdrive2]` down to the next `[` or end of file).

**On the Pi:**
4. Install rclone: `curl https://rclone.org/install.sh | sudo bash`
5. Open (or create) `~/.config/rclone/rclone.conf` and paste in the `[gdrive2]` section you copied - just append it, don't touch the existing `[gdrive]` section if there is one.
6. Verify it works: `rclone lsd gdrive2:` should print an empty list (or existing folders) with no error.
7. Test the actual export once by hand: `rclone copy /home/catreson/dane_esp_write/ gdrive2:WUTRPi-logs --progress`

After that one-time setup, the EXPORT button on the touchscreen just works - no more setup needed, and re-running it (e.g. after re-flashing the SD card) just means repeating steps 4-6 with the same already-authorized `[gdrive2]` section from your laptop, no new Google sign-in required.

If you'd rather avoid copying config files around, the alternative is running `rclone authorize "drive"` on your laptop and pasting the printed token into `rclone config` on the Pi when it asks for `config_token` (after answering `n` to "Use auto config?") - but pasting a long token over an SSH session can be finicky, so the copy-the-config-file route above is usually less error-prone.

![image](https://drive.google.com/uc?export=view&id=13yYR1pqgYXPpYR2iEUEK7wSMa94LrRi7)



