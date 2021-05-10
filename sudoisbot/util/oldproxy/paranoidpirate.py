#!/usr/bin/python3 -u

from argparse import ArgumentParser

from sudoiszmq.paranoidpirate import MajorDomo
from sudoisbot.common import init

def main():
    parser = ArgumentParser(add_help=False)
    parser.add_argument("-m", "--router-mandatory", action="store_true")
    config, args = init(__name__, parser)

    frontend_addr = config['zmq_frontend']
    backend_addr = config['zmq_backend']

    md = MajorDomo(args.router_mandatory)
    md.bind(frontend_addr, backend_addr)
    return md.mediate()


if __name__ == "__main__":
    main()
