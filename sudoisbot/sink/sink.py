#!/usr/bin/python3 -u

import os
import json
import sys
from time import sleep
from datetime import datetime

from loguru import logger
import zmq

from sudoisbot.common import init, catch
from sudoisbot.sink.simplestate import update_state


def suicide_snail(timestamp, max_delay):
    # suicide snail (move to common sub code?)
    delay = datetime.now() - datetime.fromisoformat(timestamp)
    if  min(delay.seconds, 0) > max_delay:
        logger.error(f"suicide snail: {delay.seconds} secs")
        sys.exit(13)

def msg2csv(msg):
    short_timestamp = msg['timestamp'][:19] # no millisec
    csv = f"{short_timestamp},{msg['name']},{msg['temp']}"
    return csv

def sink(addr, timeout, max_delay, state_file):
    topic = b"temp"
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
            msg = socket.recv_multipart()
        except zmq.error.Again:
            secs = timeout // 1000
            logger.warning(f"no messages after {secs} seconds")
            socket.close()
            context.destroy()
            raise


        j = json.loads(msg[1])

        csv = msg2csv(j)
        logger.bind(csv=True).log("TEMPS", csv)
        if state_file:
            try:
                update_state(j, state_file)
            except PermissionError as e:
                logger.error(e)
                raise SystemExit


@catch()
def main():
    #config = init(__name__)
    config = init("temper_sub")

    addr = config['addr']
    state_file = config.get("state_file", "")
    csv_file = config.get("csv_file", False)
    timeout = config.get("timeout", 1000*60*5) # 5 minutes
    max_delay = config.get('max_delay', 2) # seconds

    if state_file:
        logger.info(f"Maintaining state file: {state_file}")
    else:
        logger.info("Not maintaining a state file")

    # adding a new log level. INFO is 20, temps should not be logged
    # by an INFO logger
    logger.level("TEMPS", no=19, color="<yellow>", icon="🌡️")
    if csv_file:
        # adding a logger to write the rotating csv files
        # no logger timestamp since thats part of the csv data
        try:
            logger.add(csv_file,
                       level="TEMPS",
                       format="{message}",
                       rotation=config['csv_file_rotation'],
                       filter=lambda a: "csv" in a['extra'])
            logger.info(f"Saving csv to: {csv_file}")
        except PermissionError as e:
            logger.error(e)
            raise SystemExit
    else:
        logger.info("Not saving csv files")

    logger.info(f"max_delay: {max_delay} secs")

    while True:
        # endless loop to handle reconnects
        try:
            sink(addr, timeout, max_delay, state_file)
        except zmq.error.Again:
            logger.info("reconnecting after 10 seconds")
            sleep(10.0)
            continue

if __name__ == "__main__":
    main()
