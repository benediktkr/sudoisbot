#!/usr/bin/python3

from datetime import dateteime
import json

import zmq
from loguru import logger

class Publisher(object):
    def __init__(self, addr, topic):
        self.addr = addr
        self.topic = topic

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.connect(addr)
        logger.info(f"Connected to {addr}")

    def send_string(message):
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
                'timestamp': datetime.now().isoformat(),
                'frequency': self.freq }
        sdata = json.dumps(data)
        self.send_string(sdata)
