#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from itertools import islice
import logging

import telegram
from telegram import InputMediaPhoto

import common

config = common.getconfig()
logger = logging.getLogger(__name__)

def chunk(it, size=10):
    it = iter(it)
    return list(iter(lambda: list(islice(it, size)), []))

def send_to_me(text, img=None):
    me = config['bot']['me']['id']
    return send_msg(me, text, img)

def send_msg(to, text, img=None):
    bot = telegram.Bot(token=config['telegram']['api_key'])

    if config['bot']['suppress_messages']:
        return

    # if photo, send with text
    if img:
        for this in chunk(img):
            logger.info("Sending {} images".format(len(this)))
            bot.send_media_group(to, [InputMediaPhoto(a) for a in this])

    # Otherwise send a normal message
    else:
        logger.info("Sending message to {}".format(to))
        bot.send_message(
            chat_id=to,
            text=text,
            parse_mode="Markdown"
        )
