# Dynamic eye mascot Sr. Design


## Locations:
- All software is in the `Software` folder
- All 3D CAD is in the `CAD` folder
- All PCB schematics are in the `Schematic` folder




## Notes

Useful info links:
- Compute io board v3: https://www.raspberrypi.com/documentation/computers/compute-module.html#cmio
- 


Things we've checked out from lab:
- x2 micro USB cables (robert)
- x1 usb TTL adapter (ed)
- x1 mini usb cable (ed)
- x1 HDMI + DP cable (robert)
- x1 Rpi3 (luis)


How to play mp3 files through the CLI:
mpg123 gives the help menu
the -f flag controls loudness (x out of 32768)

Example:
mpg123 -f 8000 JumpingJackson.mp3


## Setup (from a stock system)

To use the built-in display+camera, copy the config files in the software folder into the boot partition (renaming them)

Software dependencies:
python3-opencv
python3-pyaudio
python3-pygame
python3-scipy
python3-picamera2


put the software.service file in:
`/etc/systemd/system/`

```
commands to start it:

sudo systemctl daemon-reload
sudo systemctl enable software.service
sudo systemctl start software.service

commands to control or restart it
sudo systemctl stop software.service
sudo systemctl restart software.service

systemctl status software.service
```
