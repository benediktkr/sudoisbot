#!/usr/bin/python3 -u

from sudoiszmq.proxy import simplepirate
from sudoisbot.common import init

def main():
    config = init(__name__)

    frontend_addr = config['zmq_frontend']
    backend_addr = config['zmq_backend']

    return simplepirate(frontend_addr, backend_addr)

if __name__ == "__main__":
    main()
