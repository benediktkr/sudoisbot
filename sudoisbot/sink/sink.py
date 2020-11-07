#!/usr/bin/python3 -u


import os
import json
from time import sleep
import dateutil.parser
from datetime import timezone

from loguru import logger
import zmq

from sudoisbot.sink import simplestate
from sudoisbot.config import read_config
from sudoisbot.network.sub import Subscriber, SubscriberTimedOutError


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
        self.disconnect()

    def send(self, msg):
        self.socket.send_multipart([self.topic, json.dumps(msg).encode()])

class Sink(object):
    def __init__(self, topics, write_path, zflux=None):
        self.zflux = zflux
        self.topics = topics
        self.setup_loggers(write_path)

        self.state_dir = write_path
        self.handlers = {
            b'temp': self.handle_temp,
            b'weather': self.handle_weather
        }

    def setup_loggers(self, writepath):
        # change to 11 or 19 to show with debug logging
        logger.level("TXT", no=9, color="<yellow>")

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
            with self.make_subscriber(addr) as sub:
                for topic, msg in sub.recv():
                    self.handle_msg(topic, msg)

        except zmq.error.Again:
            logger.info(f"timeout after {sub.rcvtimeo_secs}s..")
            raise SubscriberTimedOutError

    def handle_msg(self, topic, msg_in):
        # get a message handle if it is temp/weather which need
        # special handling right now, and format the messags
        # to the influxdb-style format.
        # when everythign sends properly formatted messages
        # we can change this logic
        handler = self.handlers.get(topic, lambda _, msg: msg)
        msg = handler(topic, msg_in)

        # universal send/write for all topics
        #self.update_db(topic, msg)         # todo: keep records in sql
        self.append_file(topic, msg)
        self.update_state(topic, msg)
        self.send_zflux(msg)

        return msg

    def handle_weather(self, topic, msg):
        # weather data was has been sent on the b'temp' topic for a while so its
        # in the same csv and influxdb measurement.
        # do this hack until i sort it out (parse the weather temps from the csv file
        # and insert to own file and measuremetn)
        legacy_msg = { 'timestamp': msg['time'],
                       'name': msg['tags']['name'],
                       'temp': msg['fields']['temp'] }

        # logs csv in rain.txt
        weather_as_temp_msg = self.handle_temp(b'temp', legacy_msg)
        # send to 'temp' measurement in influxdb
        self.send_zflux(weather_as_temp_msg)

        return msg

    def handle_temp(self, topic, msg):
        short_timestamp = msg['timestamp'][:19] # no millisec
        temp = msg['temp']
        csv = f"{short_timestamp},{msg['name']},{temp}"
        logger.bind(topic=topic).log("TXT", csv)


        ts = msg['timestamp']
        dt = dateutil.parser.parse(ts).astimezone(timezone.utc).isoformat()
        return {
            'measurement': topic.decode(),
            'tags': { 'name': msg['name'] },
            'time': dt,
            'fields': {
                "value": float(f"{float(temp):.2f}") # ugh......
            }
        }

    def update_state(self, topic, newstate):
        filename = os.path.join(self.state_dir, f"{topic.decode()}-state.json")
        simplestate.update_state(newstate, filename)

    def send_zflux(self, msg):
        if self.zflux:
            self.zflux.send(msg)

    def append_file(self, topic, msg):
        logger.bind(topic=topic).log("TXT", json.dumps(msg))


def main():
    config = read_config()

    with ZFluxClient(topic=config['zflux']['topic']) as zflux:
        zflux.connect(config['zflux']['addr'])

        sink = Sink(config['sink']['topics'], config['sink']['write_path'], zflux)
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



#from sudoisbot.sink import models
#from playhouse.db_url import connect
#from peewee import IntegrityError
#     db = connect(dburl)
#     models.db.initialize(db)

#         try:
#             if j['type'] == "weather":
#                 extra = json.dumps(j["weather"])
#             elif j["type"] == "temp":
#                 extra = json.dumps(j.get('metadata'))

#             with models.db:
#                 models.Temps.create(timestamp=j['timestamp'],
#                                     name=j['name'],
#                                     temp=j['temp'],
#                                     extra=extra)
#         except IntegrityError as e:
#             logger.error(e)
