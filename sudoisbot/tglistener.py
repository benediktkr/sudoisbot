#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

from loguru import logger

from sudoisbot import listener
from sudoisbot.common import init

if __name__ == '__main__':
    main()

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--test", action="store_true", help="who even knows")
    config = init(__name__, True, parser)

    listener.listener(config)
