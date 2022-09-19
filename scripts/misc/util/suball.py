#!/usr/bin/python3

import argparse
import sys

import zmq
from loguru import logger

from sudoisbot.common import init

if __name__ == "__main__":

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--topic", default="")
    parser.add_argument("--broker", default="broker.s21.sudo.is")
    args = parser.parse_args()

    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, b'') #args.topic.encode())


    addr = f"tcp://{args.broker}:5560"
    socket.connect(addr)
    logger.info(f"connected to '{addr}'")

    while True:
        try:
            msg = socket.recv_multipart()
        except KeyboardInterrupt:
            socket.close()
            context.destroy()
            logger.info("Exiting..")
            raise SystemExit

        #logger.info(bytedata.decode())
        logger.info(msg)
