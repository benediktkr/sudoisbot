#!/usr/bin/python3 -u

from argparse import ArgumentParser

from sudoiszmq.paranoidpirate import ParanoidPirate
from sudoisbot.common import init

def main():
    parser = ArgumentParser(add_help=False)
    parser.add_argument("--router-mandatory", action="store_true")
    config, args = init(__name__, parser)

    frontend_addr = config['zmq_frontend']
    backend_addr = config['zmq_backend']

    pp = ParanoidPirate(args.router_mandatory)
    pp.bind(frontend_addr, backend_addr)
    return pp.mediate()


    return paranoidpirate(frontend_addr, backend_addr)

if __name__ == "__main__":
    main()
