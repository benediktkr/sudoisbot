#!/usr/bin/python3 -u

import os
import json
import sys
from time import sleep
from datetime import datetime

from loguru import logger
import zmq

from sudoisbot.common import init
from temps.simplestate import update_state


def suicide_snail(timestamp, max_delay):
    # suicide snail (move to common sub code?)
    ts = datetime.fromisoformat(timestamp)
    delay = datetime.now() - ts
    if delay.seconds > max_delay:
        from sudoisbot.sendmsg import send_to_me
        send_to_me(f"suicide snail: {__name__} went and died")
        logger.error(f"suicide snail: gone and died afer {delay.seconds}s")
        # or raise something to trigger a reconnect?
        sys.exit(13)

def msg2csv(msg):
    short_timestamp = msg['timestamp'][:19] # no millisec
    csv = f"{short_timestamp},{msg['name']},{msg['temp']}"
    return csv

def sink(addr, topic, timeout, max_delay, csv_file, state_file):
    cutoff = len(topic)
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, topic)
    socket.setsockopt(zmq.RCVTIMEO, timeout)
    # Even though I'm the subscriber, I'm allowed to get this party
    # started with `bind`
    #socket.bind('tcp://*:5000')

    socket.connect(addr)
    logger.info(f"Connected to: '{addr}'")

    while True:
        try:
            bytedata = socket.recv()
        except zmq.error.Again:
            secs = timeout // 1000
            logger.warning(f"no messages after {secs} seconds")
            socket.close()
            context.destroy()
            raise

        bytejson = bytedata[cutoff:]
        j = json.loads(bytejson)

        suicide_snail(j['timestamp'], max_delay)

        if state_file:
            update_state(j, state_file)
        if csv_file:
            csv = msg2csv(j)
            logger.bind(csv=True).log("TEMPS", csv)



def main():
    config = init(__name__)

    addr = config['addr']
    state_file = config.get("state_file", "")
    csv_file = config.get("csv_file", False)
    timeout = config.get("timeout", 1000*60*5)
    max_delay = config.get('max_delay', 2) # seconds

    if state_file:
        logger.info(f"Maintaining state file: {state_file}")
    else:
        logger.info("Not maintaining a state file")

    if csv_file:
        # adding a new log level. INFO is 20, temps should not be logged
        # by an INFO logger
        logger.level("TEMPS", no=19, color="<yellow>", icon="🌡️")
        # adding a logger to write the rotating csv files
        logger.add(csv_file,
                   level="TEMPS",
                   format="{message}", # msg2csv sets timestamp from message
                   rotation=config['csv_file_rotation'],
                   filter=lambda a: "csv" in a['extra'])
        logger.info(f"Saving csv to: {csv_file}")
    else:
        logger.info("Not saving csv files")

    while True:
        # endless loop to handle reconnects
        try:
            sink(addr, b"temp: ", timeout, max_delay, csv_file, state_file)
        except zmq.error.Again:
            logger.info("reconnecting after 10 seconds")
            sleep(10.0)
            continue

if __name__ == "__main__":
    main()
