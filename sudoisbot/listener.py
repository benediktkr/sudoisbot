#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from socket import gethostname

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext import DispatcherHandlerStop, CallbackContext
import logging
import daemon

from sudoisbot.common import name_user, getconfig, logger

config = getconfig()
#logger = logging.getLogger(__name__)

unauthed_text = """
You are not authorized to use me. If you think you have any business
doing so, please talk to my person @benediktkr
"""

help_text = """
/help - this message

system:
/ruok - Check if I am OK
/where - Where am i running?
"""

def check_allowed(update, context: CallbackContext):
    if update.message.from_user.id not in config['bot']['authorized_users']:
        logger.error("Unauthorized user: {}".format(update.message.from_user))
        update.message.reply_text(unauthed_text)
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

def error(update, context):
    """Log Errors caused by Updates."""
    #logger.warning('Update "%s" caused error "%s"', update, context.error)
    logger.warning('Update caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    #logger = common.logger
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
