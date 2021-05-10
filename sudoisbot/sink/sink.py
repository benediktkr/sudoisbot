#!/usr/bin/python3 -u


import os
import json
from time import sleep
import sys

from loguru import logger
import zmq

from sudoisbot.network.sub import Subscriber, SubscriberTimedOutError
from sudoisbot.sink.models import Temperatures, Humidities, People, Weather, dbconnect


def as_bytes(astring):
    if isinstance(astring, bytes):
        return astring
    else:
        return astring.encode()


class ZFluxClient(object):
    def __init__(self, addr=None, topic=None):
        self.addr = addr
        self.topic = as_bytes(topic)

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)

        if addr:
            self.connect()

    def connect(self, addr=None):
        if not addr:
            addr = self.addr
        self.socket.connect(addr)
        logger.info(f"connected to: {addr}, emitting on topic: {self.topic}")

    def disconnect(self):
        self.socket.close()
        self.context.destroy()
        logger.debug("zflux client disconnected")

    def __enter__(self):
        if self.addr:
            self.connect(self.addr)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        #self.disconnect()
        pass

    def send(self, msg):
        self.socket.send_multipart([self.topic, json.dumps(msg).encode()])

class Sink(object):
    def __init__(self, topics, write_path, zflux=None):
        self.zflux = zflux
        self.topics = topics
        self.setup_loggers(write_path)

    def setup_loggers(self, writepath):
        # change to 11 or 19 to show with debug logging
        logger.level("TXT", no=9, color="<yellow>")
        logger.level("SINK", no=11, color="<green>")

        for topic in self.topics:
            def matcher(topic):
                def inner(arg):
                    extra_topic = arg['extra'].get('topic', b"")
                    return extra_topic == as_bytes(topic)
                return inner


            logger.add(os.path.join(writepath, f"{topic}.txt"),
                       level="TXT", format="{message}",
                       filter=matcher(topic))

    def make_subscriber(self, addr):
        return Subscriber(addr, self.topics)

    def listen(self, addr):
        try:
            # with self.make_subscriber(addr) as sub:
            #     for topic, msg in sub.recv():
            #         self.handle_msg(topic, msg)
            #
            # commented out because testing to no gracefully disconnected to get
            # publishers to buffer when sink is dead
            sub = self.make_subscriber(addr)
            sub.connect()
            for topic, msg, cached in sub.recv():
                if cached:
                    logger.info(f"got a cached {topic} message from {msg['time']}")
                self.handle_msg(topic, msg)

        except zmq.error.Again:
            logger.info(f"timeout after {sub.rcvtimeo_secs}s..")
            raise SubscriberTimedOutError

    def handle_msg(self, topic, msg):
        self.log(topic, msg)

        self.append_file(topic, msg)
        self.update_db(topic, msg)         # todo: keep records in sql
        self.send_zflux(msg)

    def update_db(self, topic, msg):
        if topic == b"temp":
            if msg['measurement'] == "temp":
                Temperatures.insert_msg(msg)
            elif msg['measurement'] == "humidity":
                Humidities.insert_msg(msg)
        elif topic == b'unifi':
            People.update_state_if_changed(msg)
        elif topic == b'weather':
            Weather.insert_msg(msg)


    def send_zflux(self, msg):
        if self.zflux:
            self.zflux.send(msg)

    def append_file(self, topic, msg):
        logger.bind(topic=topic).log("TXT", json.dumps(msg))

    def log(self, topic, msg):
        measurement = msg['measurement']


        name = msg['tags']['name']
        if 'value' in msg['fields']:
            value = f": {msg['fields']['value']}"
        else:
            value = ""
        logger.log("SINK", f"{topic}: {measurement} from '{name}'{value}")

def main(args, config):

    db = dbconnect(**config['mysql'])

    with ZFluxClient(topic=config['zflux']['topic']) as zflux:
        zflux.connect(config['zflux']['addr'])

        write_path = args.write_path or config['sink']['write_path']

        sink = Sink(config['sink']['topics'], write_path, zflux)
        while True:
            try:
                addr = config['sink']['addr']
                sink.listen(addr)
            except SubscriberTimedOutError:
                sleep(1.0)
                logger.info("reconnecting")
            except KeyboardInterrupt:
                logger.info("ok ill leave then")
                return

def suicide_snail(timestamp, max_delay):
    # suicide snail (move to common sub code?)
    delay = datetime.now() - datetime.fromisoformat(timestamp)
    if  min(delay.seconds, 0) > max_delay:
        logger.error(f"suicide snail: {delay.seconds} secs")
        raise SystemExit("suicide snail")
