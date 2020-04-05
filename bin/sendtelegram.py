#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import fileinput
import logging

from sudoisbot.sendmsg import send_msg
from sudoisbot import common

logger = common.getlogger()
logger.info("NO")
def main():
    config = common.getconfig('bot')
    logger.info(config['people']['ernesto'])

    parser = argparse.ArgumentParser(
        "Telegram bot @sudoisbot send message",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-m",
        "--message",
        required=False,
        help="Message to send"
    )
    parser.add_argument(
        "-t",
        "--to",
        help="Whom to message (userid/chatid)",
        default=config['me']['username']
    )
    parser.add_argument(
        "--code",
        help="format markdown as code",
        action='store_true',
        default=False
    )
    args = parser.parse_args()


    if args.message:
        text = args.message
    else:
        stdin = fileinput.input('-')
        text = "\n".join(stdin)

    if args.code:
        text = common.codeblock(text)

    if text:
        send_msg(config['people'][args.to], text)

if __name__ == "__main__":
    main()
