#!/usr/bin/python3 -u

from argparse import ArgumentParser

from sudoiszmq.majordomo import Broker
from sudoisbot.common import init

def main():
    parser = ArgumentParser(add_help=False)
    parser.add_argument("-m", "--router-mandatory", action="store_true")
    config, args = init(__name__, parser)

    zmq_listen = config['zmq_listen']

    broker = Broker(args.router_mandatory)
    broker.bind(zmq_listen)
    return broker.mediate()


if __name__ == "__main__":
    main()
