#!/usr/bin/python3 -u

import argparse
import os
import json
import sys

from loguru import logger
import zmq

from sudoisbot.common import getconfig
from temper.simplestate import update_state

def msg2csv(msg):
    short_timestamp = msg['timestamp'][:19] # no millisec
    csv = f"{short_timestamp},{msg['name']},{msg['temp']}"
    return csv

def sink(addr, csv_file, state_file):
    if state_file:
        logger.info(f"Maintaining state file: {state_file}")
    else:
        logger.info("Not maintaining a state file")

    if csv_file:
        logger.info(f"Saving csv to: {csv_file}")
    else:
        logger.info("Not saving csv files")


    timeout = 1000*60*5
    marker = b"temp: "
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, marker)
    socket.setsockopt(zmq.RCVTIMEO, timeout)
    # Even though I'm the subscriber, I'm allowed to get this party
    # started with `bind`
    #socket.bind('tcp://*:5000')

    socket.connect(addr)

    config = getconfig("temper_sub")

    logger.info(f"Connected to: '{addr}'")

    cutoff = len("temp: ")
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
        #logger.info(j)

        if state_file:
            update_state(j, state_file)
        if csv_file:
            csv = msg2csv(j)
            logger.bind(csv=True).success(csv)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    config = getconfig(__name__)
    addr = config['addr']
    state_file = config.get("state_file", "")
    csv_file = config.get("csv_file", False)

    if not args.verbose:
        # disable printing debug logging
        logger.remove()

    logger.debug(config)

    # adding a logger to write the rotating csv files
    logger.add(csv_file,
               format="{message}", # msg2csv sets timestamp from message
               rotation=config['csv_file_rotation'],
               filter=lambda a: "csv" in a['extra'])

    sink(addr, csv_file, state_file)

if __name__ == "__main__":
    main()
