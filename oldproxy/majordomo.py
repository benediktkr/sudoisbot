#!/usr/bin/python3 -u

from argparse import ArgumentParser

from sudoiszmq.majordomo import MajorDomo
from sudoisbot.common import init

def main():
    parser = ArgumentParser(add_help=False)
    parser.add_argument("-m", "--router-mandatory", action="store_true")
    config, args = init(__name__, parser)

    zmq_listen = config['zmq_listen']

    md = MajorDomo(args.router_mandatory)
    md.bind(zmq_listen)
    return md.mediate()


if __name__ == "__main__":
    main()
