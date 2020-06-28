#!/usr/bin/env python3

from loguru import logger

from sudoisbot.unifi import UnifiApi
from sudoisbot.common import init

def show_clients():
    config = init("unifi")
    api = UnifiApi(config)
    for client in api.get_clients_short():
        logger.info(client)
