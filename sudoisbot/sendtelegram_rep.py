#!/usr/bin/python3 -u

import json
from datetime import datetime

from loguru import logger
import zmq

from sudoisbot.sendmsg import send_to_me
from sudoisbot.common import init

def sendtelegram_rep(dealer):
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.connect(dealer)
    logger.info(f"Connected to '{dealer}'")

    while True:
        bytedata = socket.recv()
        j = json.loads(bytedata)

        # super simple for now
        logger.debug(j)
        msg = send_to_me(j['message'])
        reply = {'timtestamp': datetime.now().isoformat(),
                 'sent': True,
                 'tg_message_id': msg['mesage_id']}
        socket.send_string(json.dumps(reply))

def main():
    config = init(__name__)
    dealer = config['dealer']

    sendtelegram_rep(dealer)
