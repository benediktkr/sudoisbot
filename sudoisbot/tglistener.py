#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
    logger.info("starting telegram listener..")

    retries = 10
    retry_sleep = 60
    for _ in range(retries):
        try:
            listener.listener(config)
        except (NetworkError) as e:
            logger.warning(f"start failed: '{e.message}', retrying..")
            sleep(retry_sleep)
            continue
        except Exception as e:
            logger.error("eneded up in the catch all")
            logger.exception(e)
            logger.error(f"exception was {type(e)}")
            logger.error("exiting")
            import sys
            sys.exit(13)
    else:
        logger.error(f"giving up after {retries} tries.")
