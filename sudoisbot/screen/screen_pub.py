#!/usr/bin/python3 -u

# ansible for now

import argparse
from datetime import datetime
from os import path
import sys

from loguru import logger

from sudoisbot.network.pub import Publisher
from sudoisbot.sink import simplestate
from sudoisbot.common import init, catch, chunk

def bark():
    import random
    numberofwoofs = random.randint(1,3)
    woofs = "  " + ", ".join(["woof"] * numberofwoofs)
    return woofs


class ScreenPublisher(Publisher):
    def __init__(self,
                 addr, freq=60, rot=0, statedir=None,
                 noloop=False, test=False):
        super().__init__(addr, b"eink", "screen_pub", freq)

        self.freq = freq
        self.rotation = rot
        self.noloop = noloop
        self.test = test
        if statedir is None: self.statedir = "/dev/shm"
        else: self.statedir = statedir

        self.first_loop = True

    def get_recent_state(self, kind='temps'):
        state_file = path.join(
            self.statedir, simplestate.states[kind])
        return simplestate.get_recent(state_file)

    def weather_short(self, location):
        state = self.get_recent_state('temps')
        return state[location]['weather']['desc']

    def make_temps(self):
        l = list()

        state = self.get_recent_state('temps')

        for a in ['bedroom', 'outdoor', 'livingroom', 'ls54']:
            try:
                temp = f"{state[a]['temp']:.1f}"
            except KeyError:
                logger.warning(f"no value for '{a}'")
                temp = "    "
            shortname = a.replace('room', 'r')
            l.append(f"{shortname}: {temp} C")

        fill = max([len(a) for a in l])
        chunks = chunk([a.rjust(fill) for a in l], 2)

        temp_rows = list()
        for row in chunks:
            temp_rows.append(" | ".join(row))
        return "\n".join(temp_rows)

    def publish(self):
        temps = self.make_temps()
        try:
            weather = self.weather_short("fhain")
        except KeyError:
            logger.warning("no weather data for 'fhain'")
            weather = "error: no weather data for 'fhain'"

        halfway = 18
        weather_size = len(weather)
        padding = max(halfway - (weather_size // 2), 0)

        weth =  " "*padding + weather
        rona =  "      wash hands and shoes off  "
        woof =  "      " + bark()
        text = temps + '\n\n' + weth + '\n\n' + rona #+ '\n' + woof

        # add back logic to turn update intervals down pr stop when
        # nodody is home
        data = {
            'name': "screen_pub",
            'text': text,
            'timestamp':  datetime.now().isoformat(),
            'rotation': self.rotation,
            'min_update_interval': 15*60, # 15m
            'force_update': self.first_loop or self.noloop
        }

        self.pub(data)

        if data['force_update']:
            logger.warning("forced an update")

        if self.noloop:
            raise StopIteration
        self.first_loop = False

@catch
def main():

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--noloop", action="store_true")
    parser.add_argument("--rot", type=int)

    config, args = init(__name__, parser)
    addr = config['addr']
    rot = config['rotation'] if not args.rot else args.rot
    #people_home = config['people_home']
    noloop = args.noloop


    with ScreenPublisher(addr, noloop=noloop, rot=rot) as publisher:
        publisher.loop()



if __name__ == "__main__":
    sys.exit(main())
