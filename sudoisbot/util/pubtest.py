#!/usr/bin/python3

import time

import zmq
from loguru import logger

from sudoisbot.common import init

if __name__ == "__main__":

    config = init('pubtest',  fullconfig=True)
    topic = b"test"

    context = zmq.Context()
    socket = context.socket(zmq.PUB)

    addr = config['temper_pub']['addr']
    socket.connect(addr)
    logger.info(f"connected to '{addr}'")

    for _ in range(20):
        msg = [topic, b"testing multipart send"]

        result = socket.send_multipart(msg)
        logger.info(result)

        try:
            time.sleep(0.5)
        except KeyboardInterrupt:
            socket.close()
            context.destroy()
            logger.info("Exiting..")
            raise SystemExit
