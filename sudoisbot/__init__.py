__version__ = '0.4.4'

import argparse
import os
import sys

from sudoisbot.config import read_config


"""
tglistener = "sudoisbot.tglistener:main"
sendtelegram = "sudoisbot.sendtelegram:main"

# these will pretty much only be run while developing so just use
# poetry run python unifi/clients.py
# or something like that
#recenttemps = "sudoisbot.recenttemps:main"
#unifi_clients = "sudoisbot.unifi_clients:show_clients"
#graphtemps = "sudoisbot.sink.graphtemps:main"

"""


def run_temp_pub(args, config):
    import sudoisbot.sensors.temp_pub
    return sudoisbot.sensors.temp_pub.main(config)

def run_sink(args, config):
    import sudoisbot.sink.sink
    return sudoisbot.sink.sink.main(args, config)

def run_proxy(args, config):
    from sudoisbot.network import proxy
    return proxy.main_buffering(args, config)

def run_weather_pub(args, config):
    from sudoisbot.apis import weather_pub
    return weather_pub.main(config)

def run_screen_pub(args, config):
    from sudoisbot.screen import screen_pub
    return screen_pub.main(args, config)

def run_unifi_pub(args, config):

    from sudoisbot.apis import unifi
    if args.show_clients:
        return unifi.show_clients(config)
    else:
        return unifi.main(config)

def run_rain_pub(args, config):
    from sudoisbot.sensors import rain_pub
    return rain_pub.main(config)

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # will default to env var for config path, and allow
    # overriding with --config
    env_confpath = os.environ.get("SUDOISBOT_CONF", None)
    parser.add_argument("--config", default=env_confpath,
                        help="overrides default with $SUDOISBOT_CONF if set")
    subparser = parser.add_subparsers(dest="cmd")
    subparser.required = True

    parser_sink = subparser.add_parser('sink', help="start sink")
    parser_sink.add_argument("--write-path")
    parser_sink.set_defaults(func=run_sink)

    parser_proxy = subparser.add_parser('proxy', help="start proxy")
    parser_proxy.add_argument('--forwarder', action='store_true')
    parser_proxy.add_argument('--capture', action='store_true')
    parser_proxy.set_defaults(func=run_proxy)

    parser_temp_pub = subparser.add_parser('temp_pub', help="start temp_publisher")
    parser_temp_pub.set_defaults(func=run_temp_pub)

    parser_rain_pub = subparser.add_parser('rain_pub', help="start rain_pub")
    parser_rain_pub.set_defaults(func=run_rain_pub)

    parser_screen_pub = subparser.add_parser('screen_pub', help="start screen_pub")
    parser_screen_pub.add_argument("--no-loop", action="store_true")
    parser_screen_pub.add_argument("--dry-run", action="store_true")
    parser_screen_pub.add_argument("--rotation", type=int)
    parser_screen_pub.add_argument("--statedir")
    parser_screen_pub.set_defaults(func=run_screen_pub)

    parser_weather_pub = subparser.add_parser('weather_pub', help="start weather_pub")
    parser_weather_pub.set_defaults(func=run_weather_pub)

    parser_unifi_pub = subparser.add_parser('unifi_pub', help="start unifi_pub")
    parser_unifi_pub.add_argument("--show-clients", action="store_true")
    parser_unifi_pub.set_defaults(func=run_unifi_pub)


    args = parser.parse_args()
    config = read_config(args.config)

    #if args.cmd not in config['allowed_cmds']:
    #    parser.error(f"config {config['file_path']} is not configured for '{cmd}'")

    rc = args.func(args, config)
    sys.exit(rc)

def ruok():
    # healthcheck not yet implemented
    sys.exit(0)
