#!/usr/bin/python3 -u

import json
from datetime import datetime
import platform
import argparse

import zmq
from temper.temper import Temper
from loguru import logger

from sudoisbot.common import init

# TODO:
# use tmpfs on raspi for state
# set up ntp on raspbi

class TemperNotConnectedError(Exception): pass

def temper_pub(name, addr):
    os_ = platform.system()
    if not os_.startswith("Linux"):
        raise OSError(f"platform '{os_}' not supported for temper")

    # to limit number of messages held in memory:
    # ZMQ_HWM - high water mark. default: no limit
    # http://api.zeromq.org/2-1:zmq-setsockopt

    # And even though I'm the publisher, I can do the connecting rather
    # than the binding
    #socket.connect('tcp://127.0.0.1:5000')

    temper = Temper()
    t = temper.read()
    logger.trace(t)
    try:
        data = {
            'name': name,
            'temp': t[0]['internal temperature'],
            'timestamp': datetime.now().isoformat()
        }
    except KeyError:
        # seems to happen intermittently
        logger.error(t)
    except IndexError:
        # temper.read() returned an empty list
        raise TemperNotConnectedError("no temper device connected")

    sdata = json.dumps(data)
    logger.debug(sdata)

    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.connect(addr)
    logger.debug(f"Connected to {addr}")

    socket.send_string(f"temp: {sdata}")

    socket.close()
    context.destroy()

def main():
    parser = argparse.ArgumentParser(
        description="emit temp data from Temper, designed for cron",
        add_help=False)
    parser.add_argument("--name", help="set temper name")

    config, args = init(__name__, parser)

    addr = config['addr']
    name = config['name'] if not args.name else args.name

    logger.debug(f"emitting data as '{name}'")

    try:
        temper_pub(name, addr)
    except (OSError, TemperNotConnectedError) as e:
        logger.error(e)

if __name__ == "__main__":
    main()
