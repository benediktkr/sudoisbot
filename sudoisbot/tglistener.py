#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from loguru import logger

from sudoisbot import listener
from sudoisbot.common import init

if __name__ == '__main__':
    main()

def main():
    config = init(__name__, fullconfig=True)

    listener.listener(config)
