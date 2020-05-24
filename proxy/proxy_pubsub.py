#!/usr/bin/python3 -u

from proxy.proxy import pubsub
from sudoisbot.common import init

def main():
    config = init(__name__)

    frontend_addr = config['zmq_frontend']
    backend_addr = config['zmq_backend']

    return pubsub(frontend_addr, backend_addr)

if __name__ == "__main__":
    main()
