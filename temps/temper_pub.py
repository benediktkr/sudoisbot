#!/usr/bin/python3 -u

import json
from datetime import datetime
import platform
import argparse
import time
import sys

import zmq
from temper.temper import Temper
from loguru import logger

from sudoisbot.common import init

# TODO:
# use tmpfs on raspi for state
# set up ntp on raspbi

class TemperNotConnectedError(Exception): pass

def temper_pub(name, addr, sleep):
    os_ = platform.system()
    if not os_.startswith("Linux"):
        raise OSError(f"platform '{os_}' not supported for temper")

    # to limit number of messages held in memory:
    # ZMQ_HWM - high water mark. default: no limit
    # http://api.zeromq.org/2-1:zmq-setsockopt

    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.connect(addr)
    logger.info(f"Connected to {addr}")

    # And even though I'm the publisher, I can do the connecting rather
    # than the binding
    #socket.connect('tcp://127.0.0.1:5000')

    temper = Temper()
    # this blocks long enough to give socket.connect time to
    # finish the connection on my network, at most we will lose the
    # first datapoint which is fine
    while True:
        t = temper.read()
        logger.trace(t)
        try:
            data = {
                'name': name,
                'temp': t[0]['internal temperature'],
                'timestamp': datetime.now().isoformat(),
                'frequency': sleep
            }
        except KeyError:
            # seems to happen intermittently
            logger.error(t)
            timer.sleep(sleep)
        except IndexError:
            # temper.read() returned an empty list
            raise TemperNotConnectedError("no temper device connected")

        sdata = json.dumps(data)

        logger.debug(sdata)
        socket.send_string(f"temp: {sdata}")

        try:
            time.sleep(sleep)
        except KeyboardInterrupt:
            logger.info("Closing socket and destroying context")
            socket.close()
            context.destroy()
            raise

def main():
    parser = argparse.ArgumentParser(
        description="emit temp data from Temper, designed for cron",
        add_help=False)
    parser.add_argument("--name", help="set temper name")
    parser.add_argument("--sleep", type=int, default=240)

    config, args = init(__name__, parser)

    addr = config['addr']
    name = config['name'] if not args.name else args.name
    sleep = config['sleep'] if not args.sleep else args.sleep

    logger.info(f"emitting data as '{name}' every {sleep} secs")

    try:
        temper_pub(name, addr, args.sleep)
    except (OSError, TemperNotConnectedError) as e:
        logger.error(e)
        return 1
    except KeyboardInterrupt:
        logger.warning("Caught C-c, exiting..")
        return 0

if __name__ == "__main__":
    sys.exit(main())
