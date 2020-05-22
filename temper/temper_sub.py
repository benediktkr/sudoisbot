#!/usr/bin/python3 -u
import os
import json

from loguru import logger
import zmq

from sudoisbot.common import getconfig
from temper.simplestate import update_state

class UnsafeNameError(Exception): pass

def safe_name(msg):
    # some extra non-alnum characters that could be in names
    extra = ['-', '_']
    safe_name = "".join([a for a in msg['name'] if a.isalnum() or a in extra])
    if not len(safe_name) > 1:
        logger.error("unsafe name: '{}'", msg['name'])
        raise UnsafeNameError
    if safe_name != msg['name']:
        logger.warning("unsafe name '{}' rewritten to '{}'",
                       msg['name'], safe_name)
    return safe_name

def msg2csv(msg):
    short_timestamp = msg['timestamp'][:19] # no millisec
    csv = f"{short_timestamp},{msg['temp']}"
    return csv

def sink(addr, csv_dir, state_file):
    if state_file:
        logger.info(f"Maintaining state file: {state_file}")
    else:
        logger.info("Not maintaining a state file")

    if csv_dir:
        logger.info(f"Saving csvfiles to: {csv_dir}")
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
        if csv_dir:
            csv = msg2csv(j)
            try:
                name = safe_name(j)
            except UnsafeNamError:
                continue
            csvfile = os.path.join(csv_dir, name + ".csv")

            # i dont think we can run out of handlers?
            # or just reuse the same handler
            # a way around would be to not inssit on use the
            # reported name as a filename to save space (why am i doing that?)
            # also:
            # format='...{time:YYYY-MM-DD HH:mm:ss.SSS}...'
            # rewrite to use one file per day/week/month (use rotation)
            # csv format:
            #  HH-mm-ss, name, temp
            handler = logger.add(
                csvfile,
                format="{message}",
                rotation="1 KB",  # testing feature
                filter=lambda a: "csv" in a['extra'])
            logger.bind(csv=True).success(csv)
            logger.remove(handler)

def main():
    config = getconfig("temper_sub")

    logger.info(config)

    addr = config['addr']
    csv_dir = config.get("csv_dir", "")
    state_file = config.get("state_file", "")

    sink(addr, csv_dir, state_file)

if __name__ == "__main__":
    main()
