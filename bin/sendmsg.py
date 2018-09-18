#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import argparse
import fileinput

from sudoisbot.sendmsg import send_msg
from sudoisbot import common

config = common.getconfig()

parser = argparse.ArgumentParser(
    "Telegram bot @sudoisbot send message",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
group = parser.add_mutually_exclusive_group(
    required=True
)
group.add_argument(
    "--stdin",
    help="Read message from stdin",
    action='store_true'
)
group.add_argument(
    "-m",
    "--message",
    help="Message to send"
)
parser.add_argument(
    "-t",
    "--to",
    help="Whom to message (userid/chatid)",
    default=config['bot']['me']['id']
)
parser.add_argument(
    "--code",
    help="format markdown as code",
    action='store_true',
    default=False
)

args = parser.parse_args()


def main():
    if args.stdin:
        stdin = fileinput.input('-')
        text = "\n".join(stdin)
    else:
        text = args.message

    if args.code:
        text = common.codeblock(text)

    send_msg(args.to, text)

if __name__ == "__main__":
    main()
