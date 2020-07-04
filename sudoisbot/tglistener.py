#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from time import sleep

from loguru import logger
from telegram.error import NetworkError

from sudoisbot import listener
from sudoisbot.common import init, catch

if __name__ == '__main__':
    main()

@catch()
def main():
    config = init(__name__, fullconfig=True)

    retries = 10
    retry_sleep = 60
    for _ in range(retries):
        try:
            logger.info("starting telegram listener..")
            listener.listener(config)
            logger.info("Exiting..")
            sys.exit(0)
        except NetworkError as e:
            logger.warning(f"start failed: '{e.message}', retrying..")
            sleep(retry_sleep)
            continue

    else:
        logger.error(f"giving up after {retries} tries.")
