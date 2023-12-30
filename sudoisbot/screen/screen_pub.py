#!/usr/bin/python3 -u

# ansible for now

from datetime import datetime, timezone
import random
import time
from dataclasses import dataclass, field
from itertools import islice

from loguru import logger

from sudoisbot.network.pub import Publisher
from sudoisbot.sink.models import Temperatures, People, Weather, dbconnect


def chunk(it, size=10):
    it = iter(it)
    return list(iter(lambda: list(islice(it, size)), []))


def bark():
    numberofwoofs = random.randint(1, 3)
    woofs = "  " + ", ".join(["woof"] * numberofwoofs)
    return woofs


@dataclass
class ScreenPublisher(Publisher):
    addr: str
    weather_location: str
    people: dict
    weather: str

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

        self.folks = list(self.people.keys())

        logger.info(f"weather location: {self.weather_location}")

    def align_center(self, msg, postprefixlen=0):
        adjusted_halfway = self.halfway - postprefixlen
        if len(msg) >= adjusted_halfway*2:
            logger.warning(f"msg '{msg}' is too long, {len(msg)} chars.")

        msg_padding = max(adjusted_halfway - (len(msg) // 2), 0)
        return " "*msg_padding + msg

    def align_right(self, msg, prefixlen=0):
        pad_length = self.halfway * 2 - len(msg) - prefixlen
        padding = " "*pad_length
        return padding + msg

    def make_weather(self):
        current = Weather.get_recent(self.weather, 30*60)
        return self.align_center(current.desc)

    def make_rain(self, weather):
        return "~?~"

    def make_people(self):
        try:
            homebodies = People.get_home_names(self.folks)

            return " ".join(homebodies)
        except ValueError as e:
            logger.error(e)
            return "- - -"

    def make_text(self):
        return random.choice(self.msgs + [self.align_center(bark())])

    def make_temps(self):
        temps = list()

        for a in ['bedroom', 'study', 'livingroom', 'ls54', 'outdoor']:
            # .replace does not mutate original string
            shortname = a.replace('room', 'r')

            try:
                t0 = time.time()
                result = Temperatures.get_recent(a, secs=30*60)
                t1 = time.time() - t0
                logger.debug(f"query for: {t1:.3f}s, name='{a}'")
                tempstr = f"{result.temp:.1f}"
                if result.temp < 10.0:
                    tempstr = " " + tempstr
                temps.append(f"{shortname}: {tempstr} C")
            except KeyError:
                logger.trace(f"no recent temp for '{a}'")
                temps.append(f"{shortname}:  --  C")

        fill = max([len(a) for a in temps])
        chunks = chunk([a.rjust(fill) for a in temps], 2)

        temp_rows = list()
        for row in chunks:
            if len(row) == 1:
                temp_rows.append(f"{row[0]} |")
            else:
                temp_rows.append(" | ".join(row))
        return "\n".join(temp_rows)

    def publish(self):
        woof =  "      " + bark()  # noqa

        weth = self.make_weather()
        temps = self.make_temps()
        # folk = self.make_people()
        folk = " "
        text = self.make_text()
        rain = self.make_rain(weth)
        text = f"{temps}\n{weth}\n{text}"

        # add back logic to turn update intervals down pr stop when
        # nodody is home
        if len(folk) > 0:
            update_interval = 15*60  # 15m
        else:
            update_interval = 66*60*6
        data = {
            'name': "screen_pub",
            'bottom_right': f"{rain} / {folk}",
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
            logger.trace(f"screen should update: \n{data['text']}")
        if self.dry_run:
            import json
            jmsg = json.dumps(data, indent=2)
            logger.warning(f"not publishing: \n{jmsg}")

            raise StopIteration

        self.pub(data)
        if self.no_loop:
            raise StopIteration


def main(args, config):
    dbconnect(**config['mysql'])
    addr = config['addr']

    # people_home = config['people_home']
    kwargs = {
        **config['screen'],
        **{
            'rotation': args.rotation,
            'people': config['people'],
            'weather': config['weather'],
            'dry_run': args.dry_run,
            'no_loop': args.no_loop
        }}
    with ScreenPublisher(addr=addr, **kwargs) as p:
        p.loop()

    return 0
