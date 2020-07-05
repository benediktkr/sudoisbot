#!/usr/bin/python3 -u

import argparse
import time
import sys

import zmq
from temper.temper import Temper as TemperBase
from loguru import logger

from sudoisbot.common import init, catch
from sudoisbot.network.pub import Publisher
from sudoisbot.temps.sensors import TemperSensor, Ds18b20Sensor
from sudoisbot.temps.sensors import supported_sensors, detect_sensor
from sudoisbot.temps.exceptions import *

# TODO:
# use tmpfs on raspi for state
# set up ntp on raspbi


class TempPublisher(Publisher):
    def __init__(self, addr, name, freq, sensor=None):
        super().__init__(addr, b"temp", name, freq)

        self.sensor = sensor
        self.sensortype = self.sensor.sensortype

        logger.info(f"emitting data from a {self.sensortype} as '{self.name}'")

    def publish(self):
        try:
            temp = self.sensor.read()
            for t in temp:
                data = { 'temp': t['temp'],
                         'metadata': { 'sensortype': self.sensortype,
                                       'firmware': t.get('firmware') } }
                # adds name, timestamp, frequency, type
                return self.send(data)

        except KeyError as e:
            if self.sensortype == "temper" and e.args[0] == 'temp':
                # seems to happen intermittently
                logger.error(t)
            else:
                raise
        except SensorDisconnectedError:
            # temper was most likely unplugged
            # disconnect handled by __exit__
            logger.warning(f"{self.sensortype} sensor unplugged, disconnecting")
            raise


def wait_for_sensor(sensortype=None):
    sleep_mode = False
    while True:
        try:
            return detect_sensor(sensortype)
        except NoSensorDetectedError:
            if not sleep_mode:
                logger.info("entering sleep mode, checking for sensors every 15m")
                sleep_mode = True
            time.sleep(15.0*60)


@catch
def main():
    parser = argparse.ArgumentParser(
        description="emit temp data from therm sensor",
        add_help=False)
    parser.add_argument("--name", help="set temper name")
    parser.add_argument("--sleep", help="publish interval", type=int, default=240)
    parser.add_argument("--sensortype", choices=supported_sensors.keys())

    config, args = init("temper_pub", parser)

    addr = config['addr']
    name = config['name'] if not args.name else args.name
    sleep = config['sleep'] if not args.sleep else args.sleep


    while True:
        try:
            sensor = wait_for_sensor(args.sensortype)

            with TempPublisher(addr, name, sleep, sensor) as publisher:
                publisher.loop()
            return 0
        except SensorDisconnectedError as e:
            # especially usb sensors can be unplugged for a short time
            # for various reasons
            logger.info("waiting 30s for sensor to come back")
            time.sleep(30.0)
            continue
        except PermissionError as e:
            logger.error(e)
            return 2
        except KeyboardInterrupt:
            logger.info("Exiting..")
            return 0

if __name__ == "__main__":
    sys.exit(main())
