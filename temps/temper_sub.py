#!/usr/bin/python3 -u

import os
import json
import sys

from loguru import logger
import zmq

from sudoisbot.common import init
from temps.simplestate import update_state

def msg2csv(msg):
    short_timestamp = msg['timestamp'][:19] # no millisec
    csv = f"{short_timestamp},{msg['name']},{msg['temp']}"
    return csv

def sink(addr, marker, timeout, csv_file, state_file):
    cutoff = len(marker)
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, marker)
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
            logger.warning(f"timed out after {secs} seconds")
            logger.warning(f"Reconnecting to {addr}")
            socket.connect(addr)

        bytejson = bytedata[cutoff:]
        j = json.loads(bytejson)

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

    sink(addr, b"temp: ", timeout, csv_file, state_file)

if __name__ == "__main__":
    main()
