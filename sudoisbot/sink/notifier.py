#!/usr/bin/python3 -u

import json
from time import sleep

from loguru import logger
import zmq

from sudoisbot.common import init
from sudoisbot.sink.simplestate import update_state
from sudoisbot.sendmsg import send_to_me

state = {
    'is_raining': False,
    'notified': False
}

def notifier(addr, topic, timeout, max_delay):
    cutoff = len(topic)
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, topic)
    socket.setsockopt(zmq.RCVTIMEO, timeout)

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
        if j.get('type', '') == "weather":
            main = j['weather']['main']
            desc = j['weather']['desc']
            name = j['name']
            logger.debug(f"weather update for {name}")


            if j['weather']['precipitation']['any']:
                state['is_raining'] = True
                if not state['notified']:
                    notification = f"{name} is raining: {main} - {desc}"
                    logger.info(notification)
                    state['notified'] = True
                    send_to_me(notification)
            else:
                if state['is_raining']:
                    notification = f"{name} stopped raining: {main} - {desc}"
                    logger.info(notification)
                    state['is_raining'] = False
                    state['notified'] = False
                    send_to_me(notification)


def main():
    #config = init(__name__)
    config = init("temper_sub")

    addr = config['addr']
    timeout = config.get("timeout", 1000*60*5) # 5 minutes
    max_delay = config.get('max_delay', 2) # seconds

    while True:
        # endless loop to handle reconnects
        try:
            notifier(addr, b"temp: ", timeout, max_delay)
        except zmq.error.Again:
            logger.info("reconnecting after 10 seconds")
            sleep(10.0)
            continue

if __name__ == "__main__":
    main()
