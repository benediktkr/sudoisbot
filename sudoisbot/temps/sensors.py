#!/usr/bin/python3

from loguru import logger
from temper.temper import Temper

import os.path

from sudoisbot.temps.exceptions import *

W1ROOT = "/sys/bus/w1/devices"
W1LIST = "w1_bus_master1/w1_master_slaves"

class TempSensorBase(object):
    pass

class TemperSensor(Temper, TempSensorBase):
    sensortype = "temper"

    @classmethod
    def get(cls):
        if cls.is_connected():
            return cls()
        else:
            raise NoSensorDetectedError

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

    def __init__(self, sensor_ids):
        def w1path(sensor_id):
            return os.path.join(W1ROOT, sensor_id, "w1_slave")
        self.sensors = [(a, w1path(a)) for a in sensor_ids]

    def _read_sensor(self, sensor):
        try:
            with open(sensor, 'r') as f:
                return f.read().splitlines()
        except FileNotFoundError:
            raise SensorDisconnectedError(sensor)

    def _parse_data(self, data):
        if not data[0].endswith("YES"):
            raise SensorDisconnectedError
        tempstr = data[1].rsplit(" ", 1)[1][2:]

        return int(tempstr)/1000.0


    def read(self):
        # just expecting one sensor now
        for sensorid, sensorpath in self.sensors():
            data = self._read_sensor(sensorpath)
            temp = self._parse_data(data)

            # figure out the rest and do checksums in the future

            yield {'temp': temp }

        else:
            raise SensorDisconnectedError(sensorid)

    @classmethod
    def get(cls):

        with open(os.path.join(W1ROOT, W1LIST), 'r') as f:
            w1_ids = f.read().splitlines()

        if not all(a.startswith("28-") for a in w1_ids) and len(w1_ids) > 0:
            raise NoSensorDetectedError

        return cls(w1_ids)

    @classmethod
    def is_connected(cls):
        return len(cls.get().sensor_ids) > 0


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
