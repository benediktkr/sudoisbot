#!/usr/bin/python3

from datetime import datetime
import json

import zmq
from loguru import logger

class Publisher(object):
    # have this class  be a context manager with the loop?
    def __init__(self, addr, topic):
        self.addr = addr
        self.topic = topic

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.connect(addr)
        logger.info(f"Connected to {addr}")

    def message(self, msg):
        base = {
            'name': self.name,
            'timestamp': datetime.now().isoformat(),
        }
        return {**msg, **base}

    def send_string(self, message):
        logger.debug(message)
        self.socket.send_string(f"{self.topic}: {message}")

class TempsPublisher(Publisher):
    def __init__(self, addr, name, freq):
        super().__init__(addr, "temp")
        self.name = name
        self.freq = freq

    def send_temp(self, temp):
        data = {'name': self.name,
                'temp': temp,
                'type': 'temp',
                'timestamp': datetime.now().isoformat(),
                'frequency': self.freq }
        sdata = json.dumps(data)
        self.send_string(sdata)

class WeatherPublisher(Publisher):
    def __init__(self, addr, name, freq):
        super().__init__(addr, "temp")
        self.name = name
        self.freq = freq

    # def message(self, weather):
    #     super().message()

    def send_weather(self, weather):
        data = {'name': self.name,
                'type': 'weather',
                'timestamp': datetime.now().isoformat(),
                'frequency': self.freq }
        data.update(weather)
        sdata = json.dumps(data)
        self.send_string(sdata)
