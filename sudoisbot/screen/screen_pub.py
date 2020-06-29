#!/usr/bin/python3 -u

# ansible for now

import argparse
import json
import time
from datetime import datetime, timedelta
import os
import sys

import dateutil.parser
import zmq
from requests.exceptions import RequestException
from loguru import logger

from sudoisbot.sink import simplestate
from sudoisbot.unifi import UnifiApi
from sudoisbot.common import init, catch

def bark():
    import random
    numberofwoofs = random.randint(1,3)
    woofs = "  " + ", ".join(["woof"] * numberofwoofs)
    return woofs

def temps_fmt(state):
    t = list()
    # weird hack to show weather last
    for k, v in sorted(state.items(), key=lambda a: a[1].get('type', '') == "weather"):
        temp = v['temp']
        if v.get('type', "") == "weather":
            desc = v['weather']['desc']
            diff = datetime.now() - datetime.fromisoformat(v['timestamp'])
            age = diff.seconds // 60
            fmt = f"{k}[{age}]: {temp} C - {desc}"

            t.append(fmt)
        else:
            fmt = f"{k}: {temp} C"
            t.append(fmt)
    return '\n'.join(t)

def people_home(unifi_config, people):
    home = set()
    try:
        api = UnifiApi(unifi_config)
        wifi_clients = api.get_client_names()
    except RequestException as e:
        logger.error(e)
        raise

    for person, devices in people.items():
        for device in devices:
            if device in wifi_clients:
                home.add(person)
    return home

def people_home_fmt(home):
    if home:
        return "home: " + ", ".join(home)
    else:
        return "nobody home"

def publisher(addr, name, sleep, rot, statef, upd_int, people, unifi, noloop):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    # just hold the last message in memory
    # screen doesnt care about missed updates
    #socket.setsockopt(zmq.ZMQ_HWM, 1)
    logger.info(f"Connected to {addr}")
    socket.connect(addr)

    # will force an update on first loop
    last_home = set()
    while True:
        home_update = False
        try:
            currently_home = people_home(unifi, people)
            home = people_home_fmt(currently_home)

            # has anyone come or gone?
            if len(currently_home) != len(last_home):
                home_update = True
            last_home = currently_home
        except RequestException:
            home = "home: error"


        try:
            state = simplestate.get_recent(statef)
            temps = temps_fmt(state)

        except ValueError as e:
            logger.error(e)
            temps = str(e)

        logger.debug(temps.replace("\n", ", "))
        logger.debug(home)

        rona =  "      wash hands and shoes off  "
        woof =  "      " + bark()
        text = temps + '\n' + home  + '\n\n' + rona + '\n' + woof

        # force more frequent updates for debugging
        #  'min_update_interval': 60
        data = {
            'name': name,
            'text': text,
            'timestamp':  datetime.now().isoformat(),
            'rotation': rot
        }
        # for debugging/dev use
        if noloop:
            data['min_update_interval'] = 0
            logger.warning("forcing update")
        # if someone came or left, force update
        elif home_update:
            logger.info("Someone came/left, forcing update")
            data['min_update_interval'] = 0
            # prevent getting stuck on forcing updates
            home_update = False
        # but if nobody is at home then lets just update every 3 hours
        elif not last_home:
            data['min_update_interval'] = 60*60*3
        # otherwise default
        else:
            data['min_update_interval'] = upd_int

        sdata = json.dumps(data)
        logger.trace(sdata)
        socket.send_string(f"eink: {sdata}")

        if noloop:
            break

        try:
            time.sleep(sleep)
        except KeyboardInterrupt:
            logger.info("Caught C-c, exiting..")
            socket.close()
            context.destroy()
            return 0

@catch()
def main():

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--noloop", action="store_true")
    parser.add_argument("--rot", type=int)

    fullconfig, args = init(__name__, parser, fullconfig=True)
    config = fullconfig["screen_pub"]
    unifi = fullconfig["unifi"]

    name = config['name']
    addr = config['addr']
    sleep = config['sleep']
    rotation = config['rotation'] if not args.rot else args.rot
    temp_state_file = config['temp_state_file']
    people_home = config['people_home']
    update_interval = config['update_interval']
    noloop = args.noloop


    return publisher(addr,
                     name,
                     sleep,
                     rotation,
                     temp_state_file,
                     update_interval,
                     people_home,
                     unifi,
                     noloop)

if __name__ == "__main__":
    sys.exit(main())
