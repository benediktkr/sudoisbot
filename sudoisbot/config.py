#!/usr/bin/python3

import sys
import os

from loguru import logger
import yaml

def setup_logger():
    if 'SUDOISBOT_LOGFILE' in os.environ:
        logfile = os.environ["SUDOISBOT_LOGFILE"]
        loglevel = os.environ.get("SUDOISBOT_LOGLEVEL", "DEBUG")
        logger.remove()
        logger.add(sys.stderr, level=loglevel)
        logger.add(logfile, level=loglevel)
        logger.debug("configured logger for env vars")


def read_config(name=None):

    # looks for config file, with the following order (default name):
    #
    # 1. file specified by environment var SUDOISBOT_CONF (name is ignored)
    # 2. .${name}.yml in the users homedir
    # 3. /etc/sudoisbot/${name}.yml
    # 5. /usr/local/etc/sudoisbot/${name}.yml
    # 6. .${name}.yml in current dir
    homedir = os.path.expanduser("~")
    if name is None:
        ymlname = "sudoisbot.yml"
    elif not name.endswith(".yml"):
        ymlname = name + ".yml"
    else:
        ymlname = name

    locations = [
        os.environ.get("SUDOISBOT_CONF", ""),
        os.path.join(homedir, "." + ymlname),
        os.path.join('/etc/sudoisbot', ymlname),
        os.path.join('/usr/local/etc/sudoisbot', ymlname),
        os.path.join(os.curdir, f".{ymlname}")
    ]
    for conffile in locations:
        try:
            with open(conffile, 'r') as cf:
                config = yaml.safe_load(cf)
            logger.debug(f"using config file: {conffile} (new format)")
            return config
        except IOError as e:

            if e.errno == 2: continue
            else: raise
    else:
        logger.error(f"No config file found")
        logger.debug(f"serached: {', '.join(locations)}")
        raise SystemExit("No config file found")
