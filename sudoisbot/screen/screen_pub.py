#!/usr/bin/python3 -u

# ansible for now

import argparse
from datetime import datetime, timezone
from os import path
import sys
import random
import time
from dataclasses import dataclass, field, asdict

from loguru import logger

from sudoisbot.network.pub import Publisher
from sudoisbot.sink import simplestate
from sudoisbot.common import chunk

def bark():
    numberofwoofs = random.randint(1,3)
    woofs = "  " + ", ".join(["woof"] * numberofwoofs)
    return woofs

@dataclass
class ScreenPublisher(Publisher):
    addr: str
    weather_location: str

    freq: int = 60
    rotation: int = 0
    statedir: str = "/dev/shm"
    msgs: list = field(default_factory=list)

    no_loop: bool = False
    dry_run: bool = False

    def __post_init__(self):
        super().__init__(self.addr, b"eink", "screen_pub", self.freq)
        if self.rotation is None:
            self.rotation = 0
        if self.dry_run:
            self.no_loop = True

        self.first_loop = True

        self.halfway = 17
        self.msgs = [self.align_center(msg) for msg in self.msgs]

        logger.info(f"weather location: {self.weather_location}")

    def align_center(self, msg):
        if len(msg) >= self.halfway*2:
            logger.warning("msg '{msg}' is too long, {len(msg)} chars.")

        msg_padding = max(self.halfway - (len(msg) // 2), 0)
        return " "*msg_padding + msg

    def align_right(self, msg):
        pad_length = self.halfway * 2 - len(msg)
        padding = " "*pad_length
        return padding + msg

    def get_recent_state(self, measurement='temp'):
        state_file = path.join(
            self.statedir, f"{measurement}-state.json")
        return simplestate.get_recent(state_file)

    def make_weather(self):
        try:
            state = self.get_recent_state('weather')
            weather = state[self.weather_location]['fields']['desc']
        except ValueError as e:
            logger.warning(e)
            weather = "[err: no recent weather info]"

        return self.align_center(weather)

    def make_rain(self):
        try:
            state = self.get_recent_state('rain')
            rains = any(v['fields']['value'] for v in state.values())
            indicator = "R" if rains else "-"
        except ValueError as e:
            logger.warning(e)
            indicator = "?"

        return self.align_right(indicator)

    def make_people(self):
        try:
            state = self.get_recent_state('people')['unifi']

            home = [k for k, v in state['fields'].items() if v]
            count = len(home)
            indicators = " ".join(home)
        except ValueError as e:
            logger.warning(e)
            indicators = "- - -"
            count = 1


        return self.align_right(indicators), count


    def make_text(self):
        return random.choice(self.msgs + [self.align_center(bark())])

    def make_temps(self):
        l = list()

        try:
            state = self.get_recent_state('temp')
        except ValueError as e:
            logger.warning(e)
            state = dict()

        for a in ['bedroom', 'study', 'livingroom', 'ls54', 'outdoor']:
            # .replace does not mutate original string
            shortname = a.replace('room', 'r')
            #shortname = a[:min(len(a), 4)]
            try:
                temp = state[a]['fields']['value']
                tempstr = f"{temp:.1f}"
                if temp < 10.0:
                    tempstr = " " + tempstr
                l.append(f"{shortname}: {tempstr} C")
            except KeyError:
                logger.trace(f"no recent temp for '{a}'")
                l.append(f"{shortname}:  --  C")


        fill = max([len(a) for a in l])
        chunks = chunk([a.rjust(fill) for a in l], 2)

        temp_rows = list()
        for row in chunks:
            if len(row) == 1:
                temp_rows.append(f"{row[0]} |")
            else:
                temp_rows.append(" | ".join(row))
        return "\n".join(temp_rows)

    def publish(self):
        woof =  "      " + bark()

        weth =  self.make_weather()
        temps = self.make_temps()
        folk, inhabitants = self.make_people()
        text = self.make_text()
        rain = self.make_rain()
        text = f"{weth}\n{temps}\n{folk}\n{text}\n{rain}"


        # add back logic to turn update intervals down pr stop when
        # nodody is home
        if inhabitants > 0:
            update_interval = 15*60 # 15m
        else:
            update_interval = 66*60*6
        data = {
            'name': "screen_pub",
            'text': text,
            'timestamp':   datetime.now(timezone.utc).isoformat(),
            'rotation': self.rotation,
            'min_update_interval': update_interval,
            'force_update': self.first_loop or self.no_loop
        }

        if self.first_loop:
            time.sleep(0.3)
            self.first_loop = False
        if data['force_update'] or self.no_loop:
            logger.warning(f"screen should update: \n{data['text']}")
        if self.dry_run:
            import json
            jmsg = json.dumps(data, indent=2)
            logger.warning(f"not publishing: \n{jmsg}")

            raise StopIteration

        self.pub(data)
        if self.no_loop:
            raise StopIteration

def main(args, config):

    addr = config['addr']

    #people_home = config['people_home']
    kwargs = {**config['screen'],
              **{
                  'rotation': args.rotation,
                  'dry_run': args.dry_run,
                  'no_loop': args.no_loop,
                  'statedir': args.statedir,
              }}

    with ScreenPublisher(addr=addr, **kwargs) as p:
        p.loop()

    return 0
