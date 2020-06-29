#!/usr/bin/python3

from datetime import datetime
import json

import zmq
from loguru import logger

class Publisher(object):
    # have this class  be a context manager with the loop?
    def __init__(self, addr, topic, name, frequency):
        self.addr = addr
        self.topic = topic
        self.name = name
        self.frequency = frequency
        self.type = self.topic


        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.connect(addr)
        logger.info(f"Connected to {addr}")

    def message(self, msg={}):
        base = {
            'name': self.name,
            'timestamp': datetime.now().isoformat(),
            'frequency': self.frequency,
            'type': self.type,
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
        self.type = "temp"

    def send(self, temp):
        data = self.message()
        data['temp'] = temp
        sdata = json.dumps(data)
        self.send_string(sdata)
