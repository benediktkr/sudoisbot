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

from sudoisbot.common import init, catch

# TODO:
# use tmpfs on raspi for state
# set up ntp on raspbi

class TemperNotConnectedError(Exception): pass
class TemperNoTempError(Exception): pass

def temper_get_temp():
    try:
        temper = Temper()
        t = temper.read()
        if t: logger.trace(t)
        # this is still just assuming that there'll just be
        # one temper device connected (and one `name` therefores as
        # well
        return t[0]
    except KeyError:
        logger.error(t)
        raise TemperNoTempError
    except IndexError:
        # temper.read() returned an empty list
        raise TemperNotConnectedError("no temper device connected")

def has_temper():
    try:
        t = temper_get_temp()
        return 'internal temperature' in t
    except TemperNotConnectedError:
        return False

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

    while True:
        # this blocks long enough to give socket.connect time to
        # finish the connection on my network, at most we will lose the
        # first datapoint which is fine
        try:
            temp = temper_get_temp()
            data = {
                'name': name,
                'temp': temp['internal temperature'],
                'timestamp': datetime.now().isoformat(),
                'frequency': sleep
            }
        except TemperNoTempError:
            # seems to happen intermittently
            logger.error(t)
            timer.sleep(sleep)
        except TemperNotConnectedError:
            # temper was most likely unplugged
            logger.warning("sensor unplugged, disconnecting")
            socket.close()
            context.destroy()
            raise

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

def has_sensor():
    # will eventually use more than just Temper sensors
    # this could be more more sophisticated
    if has_temper():
        return "temper"
    else:
        return ""


def wait_for_sensor():
    sensor = has_sensor()
    if sensor:
        logger.info(f"detected {sensor} sensor")
        return sensor
    else:
        logger.info("no sensor detected, entering sleep mode")
        while True:
            time.sleep(15*60)
            sensor = has_sensor()
            if sensor:
                logger.info(f"detected {sensor} sensor")
                return sensor

@catch()
def main():
    parser = argparse.ArgumentParser(
        description="emit temp data from Temper, designed for cron",
        add_help=False)
    parser.add_argument("--name", help="set temper name")
    parser.add_argument("--sleep", type=int, default=240)

    #config, args = init(__name__, parser)
    config, args = init("temper_pub", parser)

    addr = config['addr']
    name = config['name'] if not args.name else args.name
    sleep = config['sleep'] if not args.sleep else args.sleep

    while True:
        sensor = wait_for_sensor()
        logger.info(f"emitting data as '{name}' every {sleep} secs")

        try:
            if sensor == "temper":
                temper_pub(name, addr, args.sleep)
        except TemperNotConnectedError:
            logger.warning("temper sensor disconnected")
        except (OSError) as e:
            logger.error(e)
            return 1
        except KeyboardInterrupt:
            logger.warning("Caught C-c, exiting..")
            return 0

if __name__ == "__main__":
    sys.exit(main())
