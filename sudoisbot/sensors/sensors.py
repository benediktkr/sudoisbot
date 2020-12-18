#!/usr/bin/python3

from subprocess import check_output, STDOUT, CalledProcessError
import json
from json.decoder import JSONDecodeError
import os.path
from dataclasses import dataclass, asdict, InitVar
import time

import serial
from loguru import logger
from temper.temper import Temper

W1ROOT = "/sys/bus/w1/devices"
W1LIST = "w1_bus_master1/w1_master_slaves"

class SensorDisconnectedError(Exception): pass
class NoSensorDetectedError(Exception): pass

@dataclass
class TempSensor(object):

    name: str
    kind: str
    environment: bool

    def as_dict(self):
        return asdict(self)

    def __str__(self):
        return f"<{self.name} [kind: {self.kind}, environment: {self.environment}]>"

    @classmethod
    def from_kind(cls, **kwargs):
        kind = kwargs['kind'].lower()
        objname = kind + "sensor"
        sensorobjdict = {a.__name__.lower(): a for a in cls.__subclasses__()}

        try:
            sensorobj = sensorobjdict[objname]
            return sensorobj(**kwargs)
        except KeyError as e:
            e.args += ("unknown sensor kind", )
            raise

    @classmethod
    def autodetect(cls, name):
        """autodetects what kind of sensor is connected, only works
        when the syste has one and only one sensor conncted and only supports
        the name arg."""
        for sensorobj in cls.__subclasses__():
            try:
                sensr = sensorobj(name)
                logger.info(f"found '{sensor.kind}' sensor")
                return connected
            except (SensorDisconnectedError, NoSensorDetectedError):
                continue
        else:
            raise NoSensorDetectedError("audotdetect found no sensors connected")



@dataclass(init=True)
class TemperSensor(TempSensor):

    def _read(self):
        # this function is to abstract away some error handling and make
        # read() look nicer
        try:
            data = self._temper.read()
            if len(data) == 0:
                raise SensorDisconnectedError("temper: no data returned")
            if len(data) > 1:
                # i just have the model with one sensor. will expand if i get
                # a different model at some point.
                raise NotImplementedError("only supports Tempers with one sensor")
            return data[0]
        except FileNotFoundError as e:
            msg = f"temper: {e.args[1]}"
            logger.error(msg)
            raise SensorDisconnectedError(msg) from e
        except PermissionError as e:
            raise NoSensorDetectedError(e) from e

    def read(self):
        reading = self._read()
        try:
            return {
                'measurements': {'temp': reading['internal temperature'] }
            }
        except KeyError:
            if 'firmware' in reading:
                logger.error(f"temper usb: temp value missing from '{reading}'")
                # makes the for loop just not loop over anything
                return dict()
            else:
                raise

    def __post_init__(self):
        self._temper = Temper()
        # so we bail if temper is configured but not connected/functional
        # on start
        # call .read() because it is doing error handling, some funky errors
        # will slip past if youre trying to be smart about the exception stack
        try:
            firstreading = self._read()
            logger.trace(firstreading)
        except SensorDisconnectedError as e:
            # NoSensorDetected is already raised in ._read()
            #raise NoSensorDetectedError("temper: not connected") from e
            raise


@dataclass
class DhtSensor(TempSensor):

    dht_pin: InitVar[int]

    def __post_init__(self, dht_pin):
        if dht_pin:
            self.dht_cmd = ["dht", str(dht_pin)]
        else:
            self.dht_cmd = ["dht"]


    def read(self):
        # the dht.c binary doesnt write to stderr at the moment
        # but lets redirect stderr to stdout now in case i change
        # that so this wont break
        try:
            output = check_output(self.dht_cmd, shell=False, stderr=STDOUT)
            logger.trace(output)
            joutput = json.loads(output)

            return {
                'measurements': {
                    'temp': joutput['temp'],
                    'humidity': joutput['humidity']
                }}
        except CalledProcessError as e:
            raise SensorDisconnectedError("dht disconnected") from e


@dataclass
class Ds18b20Sensor(TempSensor):

    sensor_id: str = None
    # study: 28-0300a279f70f
    # outdoor: 28-0300a279bbc9

    def __post_init__(self):
        ds18b20s = self._list_detected_ds18b20()

        if len(ds18b20s) > 1 and self.sensor_id is None:
            raise RuntimeError("need 'sensor_id' when > 1 ds18b20's connected")

        elif self.sensor_id is None:
            self.sensor_id = ds18b20s[0]
            logger.info(f"set ds18b20 sensor_id to '{self.sensor_id}'")

        self.sensorpath = os.path.join(W1ROOT, self.sensor_id, "w1_slave")


    def _read_sensor(self):
        try:
            with open(self.sensorpath, 'r') as f:
                return f.read().splitlines()
        except FileNotFoundError:
            raise SensorDisconnectedError(f"ds18b20: '{self.sensorpath}' not found")

    def _parse_sensor_data(self):
        # YES = checksum matches
        data = self._read_sensor()
        if len(data) == 0:
            #   File "sudoisbot/temps/sensors.py", line 94, in _parse_data
            # if not data[0].endswith("YES"):
            #        └ []
            raise SensorDisconnectedError(f"ds18b20: no data")
        if not data[0].endswith("YES"):
            raise SensorDisconnectedError(f"ds18b20: got '{data}'")
        tempstr = data[1].rsplit(" ", 1)[1][2:]

        return int(tempstr)/1000.0


    def _list_detected_ds18b20(self):
        w1_listfile = os.path.join(W1ROOT, W1LIST)
        with open(w1_listfile, 'r') as f:
            w1_ids = f.read().splitlines()

        if len(w1_ids) == 0:
            raise NoSensorDetectedError("no ds18b20 sensors connected")

        if not all(a.startswith("28-") for a in w1_ids):
            # something funky is going on, if this error happens
            # then investigate
            raise NoSensorDetectedError(f"unexpected values in '{w1_listfile}': {w1_ids}")

        return w1_ids

    def read(self):
        return {
            'measurements': { 'temp': self._parse_sensor_data() },
            'meta': {'sensorid': self.sensor_id }
        }


@dataclass
class ArduinoSensor(object):

    # ard_loop_time = how often arduino should send a value in seconds
    # called 'timeout' in arduino code
    # needs a better name
    # especially since the next line also has a timeout variable
    # but thats the serial read timeout

    name: str
    kind: str
    device: InitVar[str] = "/dev/ttyUSB0" # linux is a sane default
    baudrate: InitVar[int] = 9600
    ard_loop_timeout: int = 5 # seconds


    # device = "/dev/cu.usbserial-A800eGKH"
    # device="/dev/ttyUSB0"
    def __post_init__(self, device, baudrate):
        assert self.kind == "arduino-rain"

        ser_timeout = float(self.ard_loop_timeout) # seconds
        logger.debug(f"serial timeout: {ser_timeout}s")

        try:
            self.ser = serial.Serial(device, baudrate, timeout=ser_timeout)
        except serial.SerialException as e:
            raise NoSensorDetectedError(e)


    def as_dict(self):
        return asdict(self)

    def hello(self):
        for i in range(5):
            try:
                data = self.ser.readline()
                jdata = json.loads(data)

                # 'true' is hardcoded..
                return jdata['ready']

            except (KeyError, JSONDecodeError, UnicodeDecodeError) as e:
                # need to polish this when im able to reproduce
                # maybe figure out why it happens
                logger.warning(f"got invalid json: {data}")
            except serial.serialutil.SerialException as e:
                logger.error(e)

            logger.debug(f"waiting 5s to try again {i}/5")
            time.sleep(5.0)

        else:
            raise NoSensorDetectedError("no data from arduino")


    def start(self):
        ready = self.hello()

        # \n is important !
        logger.success(f"{self.name} ready: {ready}")
        timeout_ms = self.ard_loop_timeout * 1000
        logger.info(f"getting data on {timeout_ms}ms interval")
        self.ser.write(f"{timeout_ms}\r\n".encode())


    def __enter__(self):
        # if i want to use this not as a context manager ill need
        # self.started
        self.ser.__enter__()
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.ser.__exit__(exc_type, exc_value, traceback)

    def iter_lines(self):
        while True:
            line = self.ser.readline()
            logger.trace(line)
            if line == b"":
                continue

            try:
                yield json.loads(line)
            except JSONDecodeError:
                logger.warning(f"discarging garbage: '{line}'")



@dataclass
class ArduinoRainSensor(ArduinoSensor):

    def iter_lines(self):
        for jline in super().iter_lines():
            rain = jline['digital'] == "LOW"

            yield {
                'digital': jline['digital'],
                'rain': rain
            }
