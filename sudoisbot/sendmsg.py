#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import telegram

import common

config = common.getconfig()

def send_to_me(text, img=None):
    me = config['bot']['me']['id']
    return send_msg(me, text, img)

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
