#!/usr/bin/python3

import json

from loguru import logger
import zmq

class Subscriber(object):
    def __init__(self, addr, topic, timeout=2):
        self.addr = addr
        if isinstance(topic, bytes):
            self.topic = topic
        else:
            self.topic = topic.encode("utf-8")
        self.timeout = int(timeout)

        self.context = zmq.Context()
        self.connect()

    def connect(self):
        self.socket = self.context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.SUBSCRIBE, self.topic)
        self.socket.setsockopt(zmq.RCVTIMEO, self.timeout)
        self.socket.connect(addr)



    def recv(self):
        try:
            return self.socket.recv()
        except zmq.error.Again:
            finish_this_file()
