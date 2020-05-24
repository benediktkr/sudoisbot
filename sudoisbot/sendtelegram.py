#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import fileinput

from loguru import logger

from sudoisbot.common import codeblock, init
from sudoisbot.sendmsg import send_msg, send_to_me


def main():
    parser = argparse.ArgumentParser("Send messages with as @sudoisbot")
    parser.add_argument(
        "message", help="Message to send, read stdin otherwise", nargs='?'
    )
    parser.add_argument(
        "-t",
        "--to",
        help="Whom to message, send to myself if not otherwise specified",
    )
    parser.add_argument(
        "--code",
        help="format markdown as code",
        action='store_true',
        default=False
    )
    config, args = init("telegram", argparser=parser)

    if not args.message and args.code:
        parser.error("--code not valid when using stdin")

    # use position arg if given, otherwise use stdin
    if args.message:
        if args.code:
            text = codeblock(args.message)
        else:
            text = args.message
    else:
        stdin = fileinput.input('-')
        text = codeblock("\n".join(stdin))

    # use --to if given, or send to me
    if args.to:
        send_msg(args.to, text)
    else:
        send_to_me(text)

if __name__ == "__main__":
    main()
