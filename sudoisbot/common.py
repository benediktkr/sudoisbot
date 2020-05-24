import argparse
import copy
import os
import sys

from loguru import logger
import yaml

def getconfig(section=None):
    return read_configfile("sudoisbot", section=section)

def read_configfile(name, section):
    # looks for config file, with the following order (default name):
    #
    # 1. file specified by environment var SUDOISBOT_CONF (name is ignored)
    # 2. .sudoisbot.yml in the users homedir
    # 3. /etc/sudoisbot.yml
    # 4. /etc/sudoisbot/sudoisbot.yml
    # 5. /usr/local/etc/sudoisbot.yml
    # 6. sudoisbot.yml in current dir
    homedir = os.path.expanduser("~")
    ymlname = name + ".yml"
    locations = [
        os.environ.get("SUDOISBOT_CONF", ""),
        os.path.join(homedir, "." + ymlname),
        os.path.join('/etc', ymlname),
        os.path.join('/etc', name, ymlname),
        os.path.join('/usr', 'local', 'etc', ymlname),
        os.path.join(os.curdir, ymlname)
    ]
    for conffile in locations:
        try:
            with open(conffile, 'r') as cf:
                config = yaml.safe_load(cf)
            logger.debug(f"using config file: {conffile}")
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

def init(name, fullconfig=False, extra_args=None):
    shortname = name.split(".")[-1]

    if extra_args:
        parents = [extra_args]
    else:
        parents = list()
    parser = argparse.ArgumentParser(shortname, parents=parents)
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

        # disable printing debug logs
        # these print DEBUG level with backtrace/diagnose
        if not args.verbose:
            logger.remove()

        # my defaults have backtrace/diagnose disabled
        logger.add(logfile, **config['logging'])
    except KeyError as e:
        if e.args[0] == "dir":
            logger.warning("no 'logging.dir' found, using default log sinks")
        else:
            raise

    return config
