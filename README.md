#
# SDL_Pi_AM2315
#
# AM2315 Pure Python Library

## Forked from SwitchDoc Labs March 2019 version in February 2021

This is a forked of the SwitchDoc Labs AM2315 library. This fork fixes problems in the original library code
that prevented it from running under Python 3 & adds a client that sends the readings from the sensor to [AWS IoT Core](https://aws.amazon.com/iot-core/). It makes use of the [AWS IoT Client SDK](https://github.com/aws/aws-iot-device-sdk-python-v2) to connect & send messages to IoT Core and requires credentials to be created as detailed in the [Developers Guide](https://docs.aws.amazon.com/iot/latest/developerguide/create-iot-resources.html).

## Dependencies

Tested on a Raspberry Pi Zero W, running RaspberryPi OS. Requires the following libraries to be installed:

```
sudo apt install i2c-tools python3-dev python3-pip python3-smbus libi2c-dev RPi.GPIO
```

To run the client, install the required python dependencies:

```
pip3 install -r requirements.txt
```


## Version history prior to fork
Version 1.6:  August 12, 2019 - Added adasmbus and improved I2C reliablity<BR>
Version 1.5:  June 6, 2019 - Moved to adasmbus and improved I2C reliablity<BR>
Version 1.4:  March 30, 2019 - Added PowerSave capability and improved temperature detection<BR>
Version 1.3:  February 6, 2019 - increased MaxRetries to 10 per Sopwith - Updated to Python 3 <BR>
Version 1.2:  November 26, 2018 - Added bad data filter, now can return statistics good, bad reads, bad CRC<BR>
Version 1.1:  November 14, 2018 - Added CRC Check.  Now returns -1 in CRC on CRC Fail <BR>
 

## Introduction
This is a pure python AM2315 library to replace the tentacle_pi C based library

For the SwitchDoc Labs AM2315<BR>
https://shop.switchdoc.com/products/grove-am2315-encased-i2c-temperature-humidity-sensor-for-raspberry-pi-arduino

## Installation


Place files in program directory

## testing

```
import AM2315 
sens = AM2315.AM2315()
print sens.read_temperature()
print sens.read_humidity()
print sens.read_humidity_temperature()
print sens.read_humidity_temperature_crc()
```
