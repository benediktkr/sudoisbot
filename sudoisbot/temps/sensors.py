#!/usr/bin/python3

from loguru import logger
from temper.temper import Temper


from sudoisbot.temps.exceptions import *

class TempSensorBase(object):
    @classmethod
    def get(cls):
        if cls.is_connected():
            return cls()
        else:
            raise NoSensorDetectedError


class TemperSensor(Temper, TempSensorBase):
    sensortype = "temper"

    @classmethod
    def is_connected(cls):
        try:
            temper = cls()
            return len(temper.read()) > 0
        except SensorDisconnectedError:
            return False


    def _read(self):
        # error handling
        try:
            data = super().read()
            if len(data) == 0: raise SensorDiconnectedError("temper: no data")
            return data
        except FileNotFoundError as e:
            msg = f"temper: {e.args[1]}"
            logger.error(msg)
            raise SensorDisconnectedError(msg)
        except PermissionError as e:
            msg = f"temper found but got: {e}"
            logger.error(msg)
            raise SensorDisconnectedError(msg)


    def read(self):
        data = self._read()
        mapping = {'internal temperature': 'temp',
                      'internal humidity': 'humidity',
                      'external temperature': 'temp',
                      'external humidity': 'humidity'}


        results = []
        for item in data:
            # get a dict with the old keys and their values, each of these
            # values will be their own dict

            sources = [key for key in mapping.keys() if key in item.keys()]

            base = {k: v for (k, v) in item.items() if k not in mapping.keys()}

            for oldkey in sources:
                newkey = mapping[oldkey]
                fixed = {newkey: item[oldkey], 'source': oldkey}
                results.append({**base, **fixed})

        return results


class Ds18b20Sensor(TempSensorBase):
    sensortype = "ds18b20"

    def read(self):
        raise SensorDisconnectedError

    @classmethod
    def is_connected(cls):
        return False


def detect_sensor(sensortype=None):
    if sensortype:
        logger.info(f"skipping detection, attempting to use '{sensortype}'")
        return supported_sensors[sensortype].get()

    for sensor in supported_sensors.values():
        if sensor.is_connected():
            logger.info(f"found '{sensor.sensortype}' sensor")
            return sensor.get()
    else:
        raise NoSensorDetectedError

supported_sensors = {a.sensortype: a for a in TempSensorBase.__subclasses__()}
