#!/usr/bin/python3 -u

import os
from time import time # prarnoid pirate
from collections import OrderedDict # paranoid pirate
from copy import deepcopy # paranoid pirate

from loguru import logger
import zmq

def dealer(dealer_addr, router_addr):
    context = zmq.Context()

    # facing requesters
    dealer = context.socket(zmq.DEALER)
    dealer.bind(dealer_addr)

    # facing repliers
    router = context.socket(zmq.ROUTER)
    router.bind(router_addr)

    logger.info(f"zmq dealer: {dealer_addr} [<-]--> {router_addr}")
    zmq.proxy(dealer, router)

    dealer.close()
    router.close()
    context.close()


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

def simplepirate(frontend_addr, backend_addr):
    READY = b"\x01"
    HEARTBEAT = b"\x02"

    context = zmq.Context()

    frontend = context.socket(zmq.ROUTER)
    frontend.bind(frontend_addr)

    backend = context.socket(zmq.ROUTER)
    # raises zmq.error.ZMQError when a message is sent to
    # an address thats not connected, otherwise drops
    # the message silently
    backend.setsockopt(zmq.ROUTER_MANDATORY, 1)
    backend.bind(backend_addr)

    poll_workers = zmq.Poller()
    poll_workers.register(backend, zmq.POLLIN)

    poll_both = zmq.Poller()
    poll_both.register(frontend, zmq.POLLIN)
    poll_both.register(backend, zmq.POLLIN)

    logger.info(f"simplepirate: {frontend_addr} [<-]--> {backend_addr}")

    workers = list()

    while True:
        backend.send_multipart([b'worker-0', b'', b'i ded'])
        if workers:
            socks = dict(poll_both.poll())
        else:
            logger.debug("poll_workers until worker shows up")
            socks = dict(poll_workers.poll())

        # handle worker activity on backend
        if socks.get(backend) == zmq.POLLIN:
            msg = backend.recv_multipart()
            logger.debug(f"from worker: {msg}")
            if not msg:
                logger.error("BREAKING")
                break
            address = msg[0]
            workers.append(address)

            # everything after the second (delimiter) frame is reply
            reply = msg[2:]

            # forward eerything else to a client
            if reply[0] != READY:
                logger.debug(f"to client: {reply}")
                frontend.send_multipart(reply)


        if socks.get(frontend) == zmq.POLLIN:
            # get a client request and send to first available worker
            msg = frontend.recv_multipart()
            request = [workers.pop(), b""] + msg

            logger.debug(f"from client: {msg}")
            logger.debug(f"to worker: {request}")

            backend.send_multipart(request)
