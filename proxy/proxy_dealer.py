#!/usr/bin/python3 -u

from proxy.proxy import dealer
from sudoisbot.common import init

def main():
    config = init(__name__)

    dealer_addr = config['zmq_dealer']
    router_addr = config['zmq_router']

    return dealer(dealer_addr, router_addr)
