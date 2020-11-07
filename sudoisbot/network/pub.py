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
        self.loop_sleep = self.frequency

        # TODO: decide if this is a good term or not
        self.type = self.topic.decode()


        # And even though I'm the publisher, I can do the connecting rather
        # than the binding
        #socket.connect('tcp://127.0.0.1:5000')

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        logger.debug(f"topic: {self.topic}")

    def __enter__(self):
        self.socket.connect(self.addr)
        logger.info(f"Connected to {self.addr}")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # print(exc_type)
        # print(exc_value)
        # print(traceback)

        self.socket.close()
        self.context.destroy()
        logger.info("closed socket and destroyed context")

    def publish(self):
        raise NotImplementedError("base class cant do anything")

    def start(self):
        raise NotImplementedError("base class cant do anything")

    def loop(self, sleeptime=None):
        # old method of doing while True
        # TODO: pass the freq here instead
        while True:
            try:
                self.publish()
                time.sleep(self.frequency)
            except KeyboardInterrupt:
                logger.info("ok im leaving")
                break
            except StopIteration:
                break

    def message(self, msg={}):
        base = {
            'name': self.name,
            'timestamp': datetime.now().isoformat(),
            'frequency': self.frequency,
            'type': self.type,
        }
        return {**msg, **base}

    def pub(self, data):
        jdata = json.dumps(data).encode()
        logger.trace(jdata)

        msg = [self.topic, jdata]
        self.socket.send_multipart(msg)
        return msg


    def send(self, values):
        # retire this method
        data = self.message(values)
        self.pub(data)
