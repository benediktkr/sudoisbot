#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from socket import gethostname
from collections import deque
import os
import time
from datetime import datetime, timedelta
import subprocess
from io import BytesIO

from loguru import logger
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext import DispatcherHandlerStop, CallbackContext

from sudoisbot.common import name_user, get_user_name, init
from sudoisbot.sendmsg import send_to_me
from sudoistemps import simplestate, graphtemps
from sudoisunifi.unifi import UnifiApi

unauthed_text = """
You are not authorized to use me. If you think you have any business
doing so, please talk to my person @benediktkr
"""

help_text = """
/help - this message

system:
/ruok - Check if I am OK
/where - Where am i running?

home:
/temp - get current temp

ap:
/wificlients - list of connected clients

unavailale:
/sync - sync from mathom
/bluelight - set the light to blue
/whitelight - set the light to white

"""

class ConfiguredBotHandlers(object):
    def __init__(self, config):
        self.config = config

        # unpacking some for easier referencers
        self.me = config['telegram']['me']
        self.authorized = config['listener']['authorized_users']
        logger.info(f"Authorized users: '{self.authorized}'")

        # keeping some state
        self.unauthed_attemps = set()


    def _get_temps(self):
        statefile = self.config['listener']['temp_state']
        temps = simplestate.get_recent(statefile)
        return temps

    def _temp_to_string(self, temps):
        strs = [f"{k}: `{v['temp']}`C" for (k,v) in temps.items()]
        return "\n".join(strs)

    def temp(self, update, context: CallbackContext):
        try:
            temps = self._get_temps()
            count = len(temps)
            csv = self.config['temper_sub']['csv_file']
            for name, values in temps.items():
                with BytesIO() as f:
                    stream = graphtemps.graph(name, csv, 24, f, count)
                    f.seek(0)
                    update.message.reply_photo(f)

            fmt_temps = self._temp_to_string(temps)
            update.message.reply_text(fmt_temps, parse_mode="Markdown")

            asker = name_user(update)
            logger.info(f"{asker} asked for the temp ({fmt_temps})")
        except ValueError as e:
            update.message.reply_text(str(e))
            logger.error(e)

    def auth(self, update, context: CallbackContext):
        # if this function raises an error withotu handling it
        # then the error handler is responsible for stopping
        # processing the request.
        user = update.message.from_user
        name = get_user_name(user)

        if user.username in self.authorized:
            logger.debug(user)
            if user.username != self.me['username']:
                send_to_me(f"{name}: `{update.message.text}`")
        else:
            logger.warning("Unauthorized user: {}", user)
            # stay silent and ignore the user
            #update.message.reply_text(unauthed_text)

            # then notify me, but only once
            if user.id not in self.unauthed_attemps:
                send_to_me(f"`{user}`")
                send_to_me(f"unauthorized: {name} tried talking to me")
                self.unauthed_attemps.add(user.id)
            else:
                logger.debug("already informed")

            # finally stop processing the request
            raise DispatcherHandlerStop

    def wificlients(self, update, context: CallbackContext):
        api = UnifiApi(self.config["unifi"])
        wifi_clients = api.get_clients_by_ssid()
        for ssid, clients in wifi_clients.items():
            names = [a.get('hostname', '<noname>') for a in clients]
            fmt = f'`{ssid}`:\n\n' + '\n'.join(names)

            update.message.reply_text(fmt, parse_mode="Markdown")



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

def error(update, context):
    try:
        handle_error(update, context)
    except Exception as e:
        logger.exception(e)
        raise DispatcherHandlerStop
    finally:
        logger.debug("raising DispatcherHandlerStop")
        raise DispatcherHandlerStop


def handle_error(update, context):
    # theres a bunch of interesting stuff in the context object

    # .opt(exception=True).error(....)
    logger.exception(context.error)

    # telegram errors derive from this
    # isinstance(context.error, telegram.error.TelegramError)

    if update and update.message and False:
        logger.debug(update)

        name = get_user_name(update.message.from_user)
        text = update.message.text
        e = f"{text} from {name} caused {context.error}"
        logger.error(e)

def listener(config):
    configured_handlers = ConfiguredBotHandlers(config)
    # Start the bot
    updater = Updater(config['telegram']['api_key'], use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # add a handler that will only allow certain users
    dp.add_handler(MessageHandler(
        Filters.all, configured_handlers.auth), -1)

    cmdhandlers = [
        ("start", start),
        ("help", help),
        ("ruok", ruok),
        ("where", where),
        ("sync", sync),
        ("whitelight", whitelight),
        ("bluelight", bluelight),
        ("temp", configured_handlers.temp),
        ("wificlients", configured_handlers.wificlients)
    ]

    # on different commands - answer in Telegram
    for cmd, handler in cmdhandlers:
        dp.add_handler(CommandHandler(cmd, handler))

    # on noncommand i.e message - print help
    dp.add_handler(MessageHandler(Filters.text, unknown_help))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    logger.info("Idling..")
    send_to_me("Listener started and ready..")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
