#!/usr/bin/python3 -u

import json
import time
from datetime import datetime
import os
import platform

import zmq
from temper.temper import Temper
from loguru import logger

from sudoisbot.common import init

# TODO:
# use tmpfs on raspi for state
# set up ntp on raspbi

class TemperNotConnectedError(Exception): pass

def temper_pub(temper_name, addr):
    os = platform.system()
    if not os.startswith("Linux"):
        raise OSError(f"platform '{os}' not supported for temper")

    logger.debug(f"emitting data as '{temper_name}'")

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
            'name': temper_name,
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
    config = init(__name__)

    temper_name = config['temper_name']
    addr = config['addr']

    try:
        temper_pub(temper_name, addr)
    except (OSError, TemperNotConnectedError) as e:
        logger.error(e)

if __name__ == "__main__":
    main()
