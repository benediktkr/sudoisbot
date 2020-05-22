#!/usr/bin/python3 -u

import os

from loguru import logger
import zmq

from sudoisbot.common import getconfig

def proxy(frontend_addr, backend_addr):
    context = zmq.Context()

    # facing publishers
    frontend = context.socket(zmq.XSUB)
    frontend.bind(frontend_addr)

    # facing services (sinks/subsribers)
    backend = context.socket(zmq.XPUB)
    backend.bind(backend_addr)

    logger.info(f"Starting zmq proxy({frontend_addr}, {backend_addr})")
    zmq.proxy(frontend, backend)

    # we never get here
    frontend.close()
    backend.close()
    context.close()

def main():
    config = getconfig("proxy")

    #logdir = config.get('logdir')

    frontend_addr = config['zmq_frontend']
    backend_addr = config['zmq_backend']

    return proxy(frontend_addr, backend_addr)

if __name__ == "__main__":
    main()
