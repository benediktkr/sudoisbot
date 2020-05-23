import argparse
import copy
import os
import sys

from loguru import logger
import yaml

def getconfig(section=None):
    """Simpler funcion that gets the deafult config
    file sudoisbot.yml"""
    return read_configfile("sudoisbot", section)

def read_configfile(name, section=None):
    homedir = os.path.expanduser("~")
    locations = [
        os.path.join(homedir, f".{name}.yml"),
        os.path.join('/etc', f"{name}.yml"),
        os.path.join('/etc', name, f"{name}.yml")
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
                    _section = copy.deepcopy(config[section])
                    # adding standard sections to config, but allow overrides
                    for s in ["logging"]:
                        _d = copy.deepcopy(config[s])
                        _section.setdefault(s, _d)
                    return _section
                except KeyError:
                    logger.error("Section '{}' not found in '{}'",
                                 section, conffile)
                    sys.exit(1)

            else:
                return config
        except IOError as e:
            if e.errno == 2: continue
            else: raise
    else:
        logger.error(f"Config file '{name}.yml' not found anywhere")
        sys.exit(1)

def name_user(update):
    user = update.message.from_user
    return get_user_name(user)

def get_user_name(user):
    for param in ['username', 'first_name', 'id']:
        name = getattr(user, param, False)
        if name:
            if param == "username":
                return "@" + name
            if param == "first_name":
                # try to get the last name as well
                return name + " " + gettr(user, "last_name", "")
            else:
                return name

def codeblock(text):
    if text:
        code = "```\n{}```".format(text)
        return code
    else:
        return ""

def init(name, fullconfig=False, getparser=False):
    shortname = name.split(".")[1]

    parser = argparse.ArgumentParser(shortname)
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="print debug logging")
    args = parser.parse_args()

    if fullconfig:
        config = getconfig()
    else:
        config = getconfig(shortname)

    # set up the file logger
    try:
        logdir = config['logging'].pop('dir')
        logfile = os.path.join(logdir, shortname + ".log")
        logger.debug(f"Logging to '{logfile}'")

        # dsiable priting debug logs
        if not args.verbose:
            logger.remove()

        logger.add(logfile, **config['logging'])
    except KeyError as e:
        if e.args[0] == "dir":
            logger.warning("no 'logging.dir' found, using default log sinks")
        else:
            raise

    if getparser:
        # return the parser if neded, but ideally the caller shouldnt
        # need to care about anything set by the argparser, just the conf
        return (config, parser)
    else:
        return config
