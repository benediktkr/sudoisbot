#!/usr/bin/python3

import json
import time

from loguru import logger
import zmq

class SubscriberTimedOutError(Exception): pass

def reconnect(delay=3.0):

    def wrapper(f):
        while True:
            try:
                f()
            except zmq.error.Again:
                logger.info(f"reconnecting after {delay}sec")
                time.sleep(delay)
                continue
            except KeyboardInterrupt:
                logger.info("ok fine im leaving")
                return

    return wrapper


class Subscriber(object):

    def __init__(self, addr, topics, rcvtimeo=5*60):
        if not isinstance(topics, list):
            topics = [topics]

        self.addr = addr
        self.topics = [t.encode() if isinstance(t, str) else t for t in topics]
        self.rcvtimeo_secs = int(rcvtimeo)

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.XSUB)
        self.socket.setsockopt(zmq.RCVTIMEO, self.rcvtimeo_secs * 1000)
        #logger.info(f"RCVTIMEO is {self.rcvtimeo_secs}s")
        for topic in self.topics:
            #self.socket.setsockopt(zmq.SUBSCRIBE, topic)
            self.socket.send_multipart([b"\x01" + topic])


    def connect(self, addr=None):
        self.socket.connect(self.addr)
        logger.info(f"connected to: {self.addr}, topics: {self.topics}")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.socket.close()
        self.context.destroy()
        logger.debug("closed socket and destroyed context")

    def recv(self):
        try:
            while True:
                msg = self.socket.recv_multipart()
                cached = len(msg) > 2 and msg[2] == b"cached"

                yield (msg[0], json.loads(msg[1]), cached)

        except zmq.error.Again:
            logger.warning(f"no messages in {self.rcvtimeo_secs}s")
            raise
