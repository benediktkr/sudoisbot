#!/usr/bin/python3 -u

from sudoiszmq.proxy import dealer
from sudoisbot.common import init

def main():
    config = init("proxy_dealer")

    dealer_addr = config['zmq_dealer']
    router_addr = config['zmq_router']

    print("yes")
    return dealer(dealer_addr, router_addr)

if __name__ == "__main__":

    print("...")
    main()
