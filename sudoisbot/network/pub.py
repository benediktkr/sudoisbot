#!/usr/bin/python3

from datetime import datetime
import json
import time

import zmq
from loguru import logger

class Publisher(object):
    # have this class  be a context manager with the loop?
    def __init__(self, addr, topic, name, frequency):
        self.addr = addr
        self.topic = topic
        self.name = name
        self.frequency = frequency

        # TODO: decide if this is a good term or not
        self.type = self.topic.decode()


        # And even though I'm the publisher, I can do the connecting rather
        # than the binding
        #socket.connect('tcp://127.0.0.1:5000')

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)

    def __enter__(self):
        self.socket.connect(self.addr)
        logger.info(f"Connected to {self.addr}")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # print(exc_type)
        # print(exc_value)
        # print(traceback)

        logger.debug("closing socket and destroyed context")
        self.socket.close()
        self.context.destroy()

    def publish(self):
        raise NotImplementedError("base class cant do anything")

    def loop(self):
        while True:
            try:
                self.publish()
                time.sleep(self.frequency)
            except KeyboardInterrupt:
                logger.info("Caught C-c..")
                break

    def message(self, msg={}):
        base = {
            'name': self.name,
            'timestamp': datetime.now().isoformat(),
            'frequency': self.frequency,
            'type': self.type,
        }
        return {**msg, **base}


    def send(self, temp):
        data = self.message(temp)
        jdata = json.dumps(data).encode()
        logger.debug(jdata)

        msg = [self.topic, jdata]
        self.socket.send_multipart(msg)
        return msg
