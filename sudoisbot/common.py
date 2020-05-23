import copy
import os
import logging
import sys

# until morale improves and builtin logger is gone, loguru needs to be renaed
from loguru import logger as log
import yaml

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
    """Simpler funcion that gets the deafult config
    file sudoisbot.yml"""
    return read_configfile("sudoisbot", part)

def read_configfile(name, section=None):
    homedir = os.path.expanduser("~")
    locations = [
        os.path.join(homedir, f".{name}.yml"),
        os.path.join('/etc', f"{name}.yml"),

    ]
    for conffile in locations:
        try:
            with open(conffile, 'r') as cf:
                config = yaml.safe_load(cf)
            if section:
                # i think i should use config parser, but thats
                # for a later improvement
                section = section.split(".")[-1]
                try:
                    _default = copy.deepcopy(config["default"])
                    _section = copy.deepcopy(config[section])
                    _default.update(_section)
                    return _default
                except KeyError:
                    log.error("Section '{}' not found in '{}'",
                              section, conffile)
                    sys.exit(1)

            else:
                return config
        except IOError as e:
            if e.errno == 2: continue
            else: raise
    else:
        log.error(f"Config file '{name}.yml' not found anywhere")
        sys.exit(1)

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
