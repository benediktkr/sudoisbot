import argparse
import copy
import os
import sys

from loguru import logger
import yaml

from sudoisbot.sendmsg import send_to_me

def useragent():
    import pkg_resources
    version = pkg_resources.get_distribution('sudoisbot').version
    return f"sudoisbot/{version} github.com/benediktkr/sudoisbot"



def catch():
    """Customizing loguru's @catch decorator in one place
    """
    name = sys.argv[0]
    def onerror(e):
        # this function is called after the error has been logged
        msg = f"{name} | {type(e).__name__}: {e}"

        if os.environ.get("SUDOISBOT_SYSTEMD"):
            logger.debug("sending notification of my impending death")
            try:
                send_to_me(f"`{name}` crashed with: `'{e}'`")
            except Exception as e:
                logger.error(e)
                logger.error("failed to send message, exiting..")

        else:
            print(f"(tg) {msg}")

        sys.exit(1)

    return logger.catch(onerror=onerror)


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

def init(name, argparser=None, fullconfig=False):
    # think about, how to handle library code such as sendmsg.py

    shortname = name.split(".")[-1]
    systemd = "SUDOISBOT_SYSTEMD" in os.environ
    if systemd:
        logger.debug("systemd detected")


    if isinstance(argparser, argparse.ArgumentParser):
        if argparser.add_help:
            logger.error("must set add_help=False for argparser")
            sys.exit(2)
        parents = [argparser]
        description = argparser.description
    else:
        parents = []
        description = ""

    parser = argparse.ArgumentParser(
        shortname,
        description=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=parents)

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="print info logs")
    parser.add_argument("--loglevel", help="for stderr")
    # parer.add_argument(
    #     "-d", "--debug", action="store_true", help="print debug logs"
    # )

    args = parser.parse_args()

    # this used to be further down to print logfile and config file paths
    if not args.verbose or args.loglevel:
        # disable printing debug logs
        # these print DEBUG level with backtrace/diagnose
        logger.remove()
        stderrlevel = args.loglevel.upper() if args.loglevel else "INFO"
        logger.add(sys.stderr, level=stderrlevel)

    if fullconfig:
        config = getconfig()
    else:
        config = getconfig(shortname)

    # set up the file logger
    try:
        logdir = config['logging'].pop('dir')
        logfile = os.path.join(logdir, shortname + ".log")

        # NOTE: used to disable deafult logger here

        # my defaults have backtrace/diagnose disabled
        # PermissionError if we cant write to that file
        try:
            logger.add(logfile, **config['logging'])
            logger.debug(f"Logging to '{logfile}'")
        except PermissionError:
            # little hack to ignore using logfiles if theres a permission error
            # because argparser shouldnt be used if its running with
            # systemd and should only happen during development and
            # since the config file is a bit of a mess ugh....
            if args.verbose:
                pass
            else:
                raise
    except KeyError as e:
        if e.args[0] == "dir":
            logger.warning("no 'logging.dir' found, using default log sinks")
        else:
            raise

    if argparser:
        return (config, args)
    else:
        return config
