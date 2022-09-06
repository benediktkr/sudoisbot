#!/usr/bin/python3

import json
from time import time, sleep
from socket import gethostname
from datetime import datetime, timezone

from loguru import logger

from sudoisbot.network.pub import Publisher
from sudoisbot.sensors.sensors import ArduinoRainSensor, NoSensorDetectedError


class RainPublisher(Publisher):
    def __init__(self, sensor, addr, location, freq):
        super().__init__(addr, b"rain", None, freq)

        self.sensor = sensor
        self.location = location
        self.freq = freq

        self.pub_at = time()

        self.tags = {
            'hostname': gethostname(),
            'name': self.sensor.name,
            'location':self.location,
            'kind': self.sensor.kind,
            'frequency': self.freq,
        }
        logger.info(f"emitting data as '{self.sensor.name}' every {freq}s")


    def publish(self, line):
        # LOW = water on the rain sensor, resistance has been LOWered

        msg = {
            'measurement': 'rain',
            'time': datetime.now(timezone.utc).isoformat(),
            'tags': self.tags,
            'fields': {
                'value': line['rain'],
                'digital': line['digital'],
                'value_int': int(line['rain'])
            }
        }

        logmsg = f"{msg['tags']['name']} rain: {bool(line['rain'])}"
        logger.log("RAIN", logmsg)
        self.pub(msg)


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
                    if rainline['rain']:
                        logger.warning("started raining")
                    else:
                        logger.info("stopped raining")

                self.publish(rainline)
                self.pub_at = now + self.freq

            rain_state = rainline['rain']

def main(config):
    broker = config['broker']
    freq = config['frequency']
    loc = config['location']

    log_no = config.get('sensor_log_no', 9)
    logger.level("RAIN", no=log_no, color="<green>")
    logger.info(f"logging level RAIN on no {log_no}")

    try:
        if len(config['sensors']['rain']) > 1:
            raise NotImplementedError("does not make sense at the moment")
        sensor = config['sensors']['rain'][0]

        with ArduinoRainSensor(**sensor) as rain_sensor:
            with RainPublisher(rain_sensor, broker, loc, freq) as pub:
                pub.start()

    except (IndexError, KeyError) as e:
        raise SystemExit("no rain sensors configured, exiting") from e
    except NoSensorDetectedError as e:
        logger.error(e)
        return 1

    except KeyboardInterrupt:
        logger.info("Exiting..")
        return 0


    #name = "balcony"
    #loc = "s21"
    #freq = 60



    return 0
