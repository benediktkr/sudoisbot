#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from socket import gethostname
from collections import deque
import os
import time

import subprocess

from loguru import logger
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext import DispatcherHandlerStop, CallbackContext

from sudoisbot.common import name_user, getconfig, get_user_name
from sudoisbot.sendmsg import send_to_me

config = getconfig()

unauthed_text = """
You are not authorized to use me. If you think you have any business
doing so, please talk to my person @benediktkr
"""

help_text = """
/help - this message

system:
/ruok - Check if I am OK
/where - Where am i running?

pi1:
/sync - sync from mathom
/temp - get current temp

ap:
/bluelight - set the light to blue
/whitelight - set the light to white

"""

unauthed_attemps = set()

# import logging
# class LoguruHandler(logging.StreamHandler):
#     def emit(self, record):
#         print(record.name)
#         print(dir(record))
#         print(repr(record.msg))
#         #logger.log(record.levelname, "!!" + record.msg)

# handlers = [LoguruHandler()]
# logging.basicConfig(
#     level=logging.ERROR,
#     handlers=handlers)


def check_allowed(update, context: CallbackContext):
    user = update.message.from_user
    name = get_user_name(user)

    if user.id in config['listener']['authorized_users']:
        if user.id != config['telegram']['me']['id']:
            send_to_me(f"{name}: `{update.message.text}`")
    else:
        logger.warning("Unauthorized user: {}", user)
        update.message.reply_text(unauthed_text)

        # then notify me, but only once
        if user.id not in unauthed_attemps:
            send_to_me(f"`{user}`")
            send_to_me(f"unauthorized: {name} tried talking to me")
            unauthed_attemps.add(user.id)

        # finally stop processing the request
        raise DispatcherHandlerStop


# Define a few command handlers.
def start(update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')

def unknown_help(update, context: CallbackContext):
    logger.info("{} is being rude".format(name_user(update)))
    update.message.reply_text("Unknown command")
    update.message.reply_text(help_text)

def where(update, context: CallbackContext):
    hostname = "`{}`".format(gethostname())
    update.message.reply_text(hostname, parse_mode='Markdown')
    logger.info("{} asked me where i am".format(name_user(update)))

def help(update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    update.message.reply_text(help_text)
    logger.info("{} asked me for help".format(name_user(update)))

def ruok(update, context: CallbackContext):
    """A way for me to check if it is alive"""
    logger.info("{} asked me how im ding".format(name_user(update)))
    update.message.reply_text('`imok`', parse_mode='Markdown')

def respond(update, context: CallbackContext):
    """Answer the user message."""
    update.message.reply_text(update.message.chat_id)

def sync(update, context: CallbackContext):
    #cmd = ['/bin/bash', '/home/ben/.local/bin/sync.sh']
    cmd = ['/bin/bash', '/tmp/test.sh']
    ps = subprocess.run(cmd)
    rc = ps.returncode
    if rc != 0:
        err = "`{}` returned `{}`".format(" ".join(cmd), rc)
        update.message.reply_text(err, parse_mode="Markdown")
    else:
        update.message.reply_text("synced")


def whitelight(update, context: CallbackContext):
    cmd = ['/bin/bash', '/tmp/white_light.sh']
    ps = subprocess.run(cmd)
    rc = ps.returncode
    if rc != 0:
        err = "`{}` returned `{}`".format(" ".join(cmd), rc)
        update.message.reply_text(err, parse_mode="Markdown")
    else:
        update.message.reply_text("done")
    logger.info("{} set AP light to white".format(name_user(update)))

def bluelight(update, context: CallbackContext):
    cmd = ['/bin/bash', '/tmp/blue_light.sh']
    ps = subprocess.run(cmd)
    rc = ps.returncode
    if rc != 0:
        err = "`{}` returned `{}`".format(" ".join(cmd), rc)
        update.message.reply_text(err, parse_mode="Markdown")
    else:
        update.message.reply_text("done")
    logger.info("{} set AP light to blue".format(name_user(update)))

def temp(update, context: CallbackContext):
    try:
        updated = os.path.getmtime("/srv/temps.txt")
        now = time.time()
        if updated < (now - 3600):
            raise ValueError("temperature data too old")
        with open("/srv/tempgraph.png", "rb") as graph:
            update.message.reply_photo(graph)

        with open("/srv/temps.txt") as f:
            t = deque(f, 1).pop().strip()

        text = "Current temp: `{}C`".format(t)
        update.message.reply_text(text, parse_mode="Markdown")

        logger.info("{} asked for the temp ({})".format(name_user(update), t))
    except FileNotFoundError as e:
        update.message.reply_text("temperature file doesnt exist here")
        logger.error(e)
    except ValueError as e:
        update.message.reply_text(str(e))
        logger.error(e)


errors_sent = set()
def error(update, context):
    """Log Errors caused by Updates."""

    # .opt(exception=True).error(....)
    logger.error(context.error)

    # telegram errors derive from this
    # isinstance(context.error, telegram.error.TelegramError)

    if update and update.message:
        logger.error(update)
        name = get_user_name(update.message.from_user)
        text = update.message.text
        # theres a bunch of interesting stuff in the context object
        e = f"{text} from {name} caused {context.error}"
        logger.error(e)
        if e not in errors_sent:
            # very simple, just meant to make me aware that i should
            # read the log
            send_to_me(e)
            errors_sent.add(e)

    # prevents the bot from leaking responses
    raise DispatcherHandlerStop


def main():
    """Start the bot."""
    updater = Updater(config['telegram']['api_key'], use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # add a handler that will only allow certain users
    dp.add_handler(MessageHandler(Filters.all, check_allowed), -1)

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("ruok", ruok))
    dp.add_handler(CommandHandler("where", where))
    dp.add_handler(CommandHandler("sync", sync))
    dp.add_handler(CommandHandler("whitelight", whitelight))
    dp.add_handler(CommandHandler("bluelight", bluelight))
    dp.add_handler(CommandHandler("temp", temp))

    # on noncommand i.e message - print help
    dp.add_handler(MessageHandler(Filters.text, unknown_help))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    logger.info("Idling..")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
