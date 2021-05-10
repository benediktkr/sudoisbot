#!/usr/bin/python3

import sys
import os

from loguru import logger
import yaml

def read_config(fullpath=None):
    if 'SUDOISBOT_LOGFILE' in os.environ:
        logfile = os.environ["SUDOISBOT_LOGFILE"]
        loglevel = os.environ.get("SUDOISBOT_LOGLEVEL", "INFO")
        logger.remove()
        logger.add(sys.stderr, level=loglevel)
        logger.add(logfile, level=loglevel)

    if 'SUDOISBOT_CONF' in os.environ:
        locations = [os.environ['SUDOISBOT_CONF']]
    elif fullpath is not None:
        fname = fullpath
        locations = [fullpath]
    else:
        fname = "sudoisbot.yml"
        locations = [
            os.path.join('/etc/', fname),
            os.path.join('/usr/local/etc', fname),
            os.path.join(os.curdir, fname),
            os.path.join(os.path.expanduser("~"), "." + fname)

        ]
    for conffile in locations:
        try:
            with open(conffile, 'r') as cf:
                config = yaml.safe_load(cf)

            config['file_path'] = conffile
            logger.info(f"config file: {conffile}")
            return config
        except IOError as e:

            if e.errno == 2: continue
            else: raise
    else:
        logger.error(f"config file not found: '{fname}', searched: {locations}")
        raise SystemExit("No config file found")
