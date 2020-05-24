#!/usr/bin/python3 -u

import os

from loguru import logger
import zmq

def pubsub(frontend_addr, backend_addr):
    context = zmq.Context()

    # facing publishers
    frontend = context.socket(zmq.XSUB)
    frontend.bind(frontend_addr)

    # facing services (sinks/subsribers)
    backend = context.socket(zmq.XPUB)
    backend.bind(backend_addr)

    logger.info(f"zmq pubsub proxy: {frontend_addr} -> {backend_addr}")
    zmq.proxy(frontend, backend)

    # we never get here
    frontend.close()
    backend.close()
    context.close()
