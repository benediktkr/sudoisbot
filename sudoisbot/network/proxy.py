#!/usr/bin/python3 -u

import os

from loguru import logger
import zmq

from sudoisbot.common import init
from sudoisbot.config import read_config

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

def proxy(frontend_addr, backend_addr):
    context = zmq.Context()

    # facing publishers
    frontend = context.socket(zmq.XSUB)
    frontend.bind(frontend_addr)

    # facing services (sinks/subsribers)
    backend = context.socket(zmq.XPUB)
    backend.bind(backend_addr)
    # infrom publishers of a new sink
    #backend.setsockopt(ZMQ_XPUB_VERBOSE, 1)

    logger.info(f"zmq pubsub proxy: {frontend_addr} -> {backend_addr}")
    zmq.proxy(frontend, backend)

    # we never get here
    frontend.close()
    backend.close()
    context.close()

def forwarder(frontend_addr, backend_addr, capture_addr=None):
    context = zmq.Context()

    # facing publishers
    #frontend = context.socket(zmq.XSUB)

    frontend = context.socket(zmq.SUB)
    frontend.setsockopt(zmq.SUBSCRIBE, b'')
    frontend.connect(frontend_addr)

    # facing services (sinks/subsribers)
    backend = context.socket(zmq.XPUB)
    backend.bind(backend_addr)
    # infrom publishers of a new sink
    #backend.setsockopt(ZMQ_XPUB_VERBOSE, 1)

    logger.info(f"zmq pubsub proxy: {frontend_addr} -> {backend_addr}")
    if capture_addr:
        capture = context.socket(zmq.PUB)
        capture.bind(capture_addr)
        logger.info(f"capture: {capture_addr}")
    else:
        capture = None

    zmq.proxy(frontend, backend, capture)

    # we never get here
    frontend.close()
    backend.close()
    if capture:
        capture.close()
    context.close()

def capture():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, b'')
    addr = "tcp://127.0.0.1:5561"
    socket.connect(addr)
    print("connecting to " + addr)

    while True:
        r = socket.recv_multipart()
        print(r)

        print("====")



def main_forwarder():
    # config = init("pubsub_forwarder")
    # zmq_in_connect = config['zmq_in_connect']
    # zmq_frontend = config['zmq_frontend']
    # zmq_capture = config['zmq_capture']

    zmq_in_connect = "tcp://192.168.1.2:5560"
    zmq_backend = "tcp://*:5560"
    zmq_capture = "tcp://127.0.0.1:5561"


    return forwarder(zmq_in_connect, zmq_backend, zmq_capture)


def main():
    config = read_config()
    return proxy(**config)
