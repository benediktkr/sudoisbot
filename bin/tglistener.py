#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import argparse

from sudoisbot import listener 

parser = argparse.ArgumentParser("Telegram bot @sudoisbot listener")
parser.add_argument("-d", "--daemon", action="store_true", help="Run as daemon")
args = parser.parse_args()


if __name__ == '__main__':
    if args.daemon:
        with daemon.DaemonContext():
            listener.main()
    else:
        listener.main()
