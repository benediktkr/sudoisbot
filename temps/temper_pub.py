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

# temper = Temper()
# t = temper.read()
# temp = t[0]['internal temperature']

# TODO:
# use tmpfs on raspi for state
# check for linut
# handle no temper being connected
# set up ntp on raspbi


def temper_pub(name, addr):
    os = platform.system()
    if not os.startswith("Linux"):
        raise OSError(f"platform '{os}' not supported for temper")


    context = zmq.Context()
    socket = context.socket(zmq.PUB)

    # to limit number of messages held in memory:
    # ZMQ_HWM - high water mark. default: no limit
    # http://api.zeromq.org/2-1:zmq-setsockopt

    # And even though I'm the publisher, I can do the connecting rather
    # than the binding
    #socket.connect('tcp://127.0.0.1:5000')
    socket.connect(addr)
    print(f"Connected to {addr}")

    temper = Temper()
    t = temper.read()
    try:
        data = {
            'name': name,
            'temp': t[0]['internal temperature'],
            'timestamp': datetime.now().isoformat()
        }
        sdata = json.dumps(data)
        #print(sdata)
        socket.send_string(f"temp: {sdata}")
    except KeyError:
        print(repr(t))

    socket.close()

def main():
    config = init(__name__)

    temper_name = config['temper_name']
    addr = config['addr']

    logger.debug(f"emitting data as '{temper_name}'")

    try:
        temper_pub(temper_name, addr)
    except OSError as e:
        logger.error(e)

if __name__ == "__main__":
    main()
