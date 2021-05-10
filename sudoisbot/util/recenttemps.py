#!/usr/bin/python3

from loguru import logger

from sudoisbot.common import init
from sudoisbot.sink.simplestate import get_recent


def main():
    config = init("temps", fullconfig=True)

    # terrible config format, bad programmer!
    state = config['temper_sub']['state_file']

    logger.debug(f"state file: '{state}'")

    for name, values in get_recent(state).items():
        temp = values['temp']
        logger.info(f"{name}: {temp}C")
