#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import daemon
import argparse
import logging

from sudoisbot import listener, common

logger = common.getlogger()


if __name__ == '__main__':
    main()

def main():
    parser = argparse.ArgumentParser("Telegram bot @sudoisbot listener")
    parser.add_argument("-d", "--daemon", action="store_true", help="Run as daemon")
    args = parser.parse_args()

    if args.daemon:
        with daemon.DaemonContext():
            listener.main()
    else:
        listener.main()
