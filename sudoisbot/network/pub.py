#!/usr/bin/python3

from datetime import datetime, timezone
import json
import time

import zmq
from loguru import logger

class Publisher(object):
    # have this class  be a context manager with the loop?
    def __init__(self, addr, topic, name, frequency):
        self.addr = addr
        self.name = None   # this should be phased out
        self.topic = topic
        self.frequency = frequency


        # And even though I'm the publisher, I can do the connecting rather
        # than the binding
        #socket.connect('tcp://127.0.0.1:5000')

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.set_hwm(256000) # 0 is supposdenly no limit
        logger.info(f"emitting on {self.topic} every {self.frequency}s")

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

    def loop(self):
        while True:
            try:
                self.publish()
                time.sleep(self.frequency)
            except KeyboardInterrupt:
                logger.info("ok im leaving")
                break
            except StopIteration:
                break

    def message(self, data={}):
        base = {
            'name': self.name,
            'timestamp':  datetime.now(timezone.utc).isoformat(),
            'frequency': self.frequency,
        }
        return {**data, **base}

    def pub(self, data):
        jdata = json.dumps(data).encode()
        logger.trace(jdata)

        msg = [self.topic, jdata]
        self.socket.send_multipart(msg)
        return msg


    def send(self, values):
        # retire this method
        raise NotImplementedError("use '.message()' for envelope and then '.pub()'")
        #data = self.message(values)
        #self.pub(data)
