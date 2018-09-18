#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import argparse
import fileinput

import telegram

import common

config = common.getconfig()

def send_msg(to, text, img=None):
    bot = telegram.Bot(token=config['telegram']['api_key'])

    # if photo, send with text
    if img:
        bot.send_photo(
            chat_id=to,
            photo=img,
            caption=text
        )

    # Otherwise send a normal message
    else:
        bot.sendMessage(
            chat_id=to,
            text=text,
            parse_mode="Markdown"
        )

if __name__ == "__main__":
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

    if args.stdin:
        stdin = fileinput.input('-')
        text = "\n".join(stdin)
    else:
        text = args.message

    if args.code:
        text = common.codeblock(text)

    send_msg(args.to, text)

