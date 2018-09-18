#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext import DispatcherHandlerStop
import logging
import daemon
import argparse

from common import name_user, getconfig

config = getconfig()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser("Telegram bot @sudoisbot listener")
parser.add_argument("-d", "--daemon", action="store_true", help="Run as daemon")
args = parser.parse_args()


unauthed_text = """
You are not authorized to use me. If you think you have any business
doing so, please talk to my person @benediktkr
"""

help_text = """
/ruok - Check if I am OK
"""

def check_allowed(bot, update):
    if update.message.from_user.id not in config['bot']['authorized_users']:
        logger.error("Unauthorized user: {}".format(update.message.from_user))
        update.message.reply_text(unauthed_text)
        raise DispatcherHandlerStop


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')


def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text(help_text)
    logger.info("{} asked me for help".format(name_user(update)))

def ruok(bot, update):
    """A way for me to check if it is alive"""
    update.message.reply_text('`imok`', parse_mode='Markdown')

def respond(bot, update):
    """Answer the user message."""
    update.message.reply_text(update.message.chat_id)
    

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(config['telegram']['api_key'])

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # add a handler that will only allow certain users
    dp.add_handler(MessageHandler(Filters.all, check_allowed), -1)

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("ruok", ruok))

    # on noncommand i.e message - answer the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, respond))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    if args.daemon:
        with daemon.DaemonContext():
            main()
    else:
        main()
