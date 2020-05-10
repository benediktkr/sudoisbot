import os
import yaml

import logging

JSON_FORMAT = '{"timestamp": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'

def getlogger():
    config = getconfig('bot')
    handlers = [logging.StreamHandler()]
    if config.get('logfile'):
        handlers.append(logging.FileHandler(config['logfile']))
    logging.basicConfig(
        level=logging.ERROR,
        format=JSON_FORMAT,
        handlers=handlers)

    return logging.getLogger(__name__)


def getconfig(part=None):
    homedir = os.path.expanduser("~")
    locations = [
        os.path.join(homedir, ".sudoisbot.yml"),
        os.path.join('/etc', "sudoisbot.yml"),
    ]
    for conffile in locations:
        try:
            with open(conffile, 'r') as cf:
                config = yaml.safe_load(cf)
            if part:
                return config[part]
            else:
                return config
        except IOError as e:
            if e.errno == 2: continue
            else: raise
    raise ValueError("No config file found")

def name_user(update):
    user = update.message.from_user
    for param in ['username', 'first_name', 'id']:
        name = getattr(user, param, False)
        if name:
            return name

def codeblock(text):
    if text:
        code = "```\n{}```".format(text)
        return code
    else:
        return ""

logger = getlogger()
