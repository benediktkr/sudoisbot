#!/usr/bin/python3 -u

import os

from loguru import logger
import zmq

def dealer(dealer_addr, router_addr):
    print("dealer")
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
