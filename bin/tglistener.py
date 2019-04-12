#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import daemon
import argparse
import logging

from sudoisbot import listener
from sudoisbot import common

parser = argparse.ArgumentParser("Telegram bot @sudoisbot listener")
parser.add_argument("-d", "--daemon", action="store_true", help="Run as daemon")
args = parser.parse_args()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    if args.daemon:
        with daemon.DaemonContext():
            listener.main()
    else:
        listener.main()
