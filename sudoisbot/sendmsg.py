#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from itertools import islice
import logging

import telegram
from telegram import InputMediaPhoto
from loguru import logger

from sudoisbot import common

def chunk(it, size=10):
    it = iter(it)
    return list(iter(lambda: list(islice(it, size)), []))

def send_to_me(text, img=None):
    return send_msg(None, text, img, True)

def send_msg(to, text, img=None, to_myself=False):
    text = text.replace("_", "\_")
    config = common.getconfig("telegram")
    if to_myself:
        to = config['me']['username']

    bot = telegram.Bot(token=config['api_key'])

    try:
        chat_id = config['people'][to]
        logger.debug(f"looked up '{to}', got '{chat_id}'")
    except KeyError:
        # in the future i might want to handle sending to
        # arbitrary telegram chat_id's, but at this point i doubt it
        logger.error(f"aborting, chat_id for user '{name}' is not known")
        # No need to reaise it further since the error is logged here
        return

    if config['suppress_messages']:
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
        logger.info(f"Sending message to {to} ({chat_id}): '{text}'")
        try:
            bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="Markdown"
            )
        except telegram.error.BadRequest as e:
            logger.error(e)
            return
