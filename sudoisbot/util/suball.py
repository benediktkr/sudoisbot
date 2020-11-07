#!/usr/bin/python3

import argparse

import zmq
from loguru import logger

from sudoisbot.common import init

if __name__ == "__main__":

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--topic", default="")
    # just get the config, so logger is just default config
    #config, args = init('suball', parser, fullconfig=True)

    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, b'') #args.topic.encode())

    #addr = config['temper_sub']['addr']
    addr = "tcp://broker.s21.sudo.is:5560"
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
