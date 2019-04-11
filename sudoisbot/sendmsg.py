#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import telegram
from telegram import InputMediaPhoto

import common

config = common.getconfig()

def send_to_me(text, img=None):
    me = config['bot']['me']['id']
    return send_msg(me, text, img)

def send_msg(to, text, img=None):
    bot = telegram.Bot(token=config['telegram']['api_key'])

    # if photo, send with text
    if img:
        bot.send_media_group(to, [InputMediaPhoto(a) for a in img])

    # Otherwise send a normal message
    else:
        bot.send_message(
            chat_id=to,
            text=text,
            parse_mode="Markdown"
        )
