#!/usr/bin/python3

import json
from json.decoder import JSONDecodeError
from time import time, sleep
from datetime import datetime, timezone

from loguru import logger
import serial

from sudoisbot.network.pub import Publisher

#device = "/dev/cu.usbserial-A800eGKH"
BAUDRATE = 9600


class ArduinoSensor(serial.Serial):
    def __init__(self, wait_timeout=1000, device="/dev/ttyUSB0"):
        # wait_timeout = how often arduino should send a value in ms
        # called 'timeout' in arduino code
        # needs a better name
        # especially since the next line also has a timeout variable
        # but thats the serial read timeout
        super().__init__(device, BAUDRATE, timeout=3600)
        self.wait_timeout = wait_timeout
        self.kind = "arduino"

    def start(self):
        try:
            data = self.readline()
            if not json.loads(data)['ready']:
                # 'true' is hardcoded..
                raise JSONDecodeError
        except (KeyError, JSONDecodeError) as e:
            # need to polish this when im able to reproduce
            # maybe figure out why it happens
            logger.error(f"invalid json: {data}")
            raise SystemExit

        # \n is important !
        logger.info(f"setting {self.wait_timeout} as interval")
        self.write(f"{self.wait_timeout}\r\n".encode())


    def __enter__(self):
        # if i want to use this not as a context manager ill need
        # self.started
        super().__enter__()
        self.start()
        return self

    def iter_lines(self, f=json.loads):
        while True:
            line = self.readline()
            if line == b"":
                continue
            if f is not None:
                yield f(line)
            else:
                yield line


class ArduinoRainSensor(ArduinoSensor):

    def iter_lines(self, f=json.loads):
        for jline in super().iter_lines(f):
            rain = jline['digital'] == "LOW"
            now = datetime.now(timezone.utc).isoformat()
            yield {
                'digital': jline['digital'],
                'time': now,
                'rain': rain
            }


class RainPublisher(Publisher):
    def __init__(self, sensor, addr, name, loc, freq):
        super().__init__(addr, b"rain", name, freq)

        self.sensor = sensor
        self.freq = freq
        self.pub_at = time()

        self.tags = {
            'name': name,
            'location': loc,
            'kind': self.sensor.kind
        }


        logger.info(f"emitting data as '{name}' every {freq}s")

    def publish(self, line):
        data = {
            'measurement': 'rain',
            'time': line['time'],
            'tags': self.tags,
            'fields': {
                'value': line['rain'],
                'value_int': int(line['rain'])
            }
        }

        logger.info(json.dumps(data, indent=2))
        self.pub(data)


    def start(self):
        try:
            return self._start()
        except KeyboardInterrupt:
            logger.info("ok im leaving")


    def _start(self):
        rain_state = False
        for rainline in self.sensor.iter_lines():

            #logger.debug(rainline)

            now = time()
            if now >= self.pub_at or rainline['rain'] != rain_state:

                if rainline['rain'] != rain_state:
                    logger.warning("state change!")

                self.publish(rainline)
                self.pub_at = now + self.freq

            rain_state = rainline['rain']

def main():
    addr = "tcp://broker.sudo.is:5559"
    name = "balcony"
    loc = "s21"
    freq = 60

    with ArduinoRainSensor(3000) as rain_sensor:
        with RainPublisher(rain_sensor, addr, name, loc, freq) as pub:
            pub.start()

if __name__ == "__main__":
    import sys
    sys.exit(main())
