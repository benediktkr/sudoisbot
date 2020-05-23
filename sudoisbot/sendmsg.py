#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from itertools import islice
import logging

import telegram
from telegram import InputMediaPhoto
from loguru import logger

from sudoisbot import common

config = common.getconfig()

class UnknownUserError(ValueError): pass

def chunk(it, size=10):
    it = iter(it)
    return list(iter(lambda: list(islice(it, size)), []))

def send_to_me(text, img=None):
    me = config['telegram']['me']['username']
    return send_msg(me, text, img)

def get_chat_id(name):
    try:
        chat_id = config['telegram']['people'][name]
        logger.debug(f"looked up '{name}', got '{chat_id}'")
        return chat_id
    except KeyError:
        raise UnknownUserError(f"chat_id for user '{name}' is not known")



def send_msg(to, text, img=None):
    bot = telegram.Bot(token=config['telegram']['api_key'])

    try:
        chat_id = get_chat_id(to)
    except UnknownUserError as e:
        # in the future i might want to handle sending to
        # arbitrary telegram chat_id's, but at this point i doubt it
        logger.error(e)
        # No need to reaise it further since the error is logged here
        return

    if config['telegram']['suppress_messages']:
        logger.warning("not sending, 'supress_messages' set to True")
        return

    # if photo, send with text
    if img:
        for this in chunk(img):
            logger.info(f"Sending {len(this)} images to @{to} ({chat_id})")
            photos = [InputMediaPhoto(a) for a in this]
            try:
                bot.send_media_group(chat_id, photos)
            except telegram.error.BadRequest as e:
                logger.error(e)
                return


    # Otherwise send a normal message
    else:
        logger.info(f"Sending message to @{to} ({chat_id})")
        try:
            bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="Markdown"
            )
        except telegram.error.BadRequest as e:
            logger.error(e)
            return
