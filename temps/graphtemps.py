#!/usr/bin/env python3

from collections import deque, defaultdict
import argparse
import sys
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy
from loguru import logger

from temps.simplestate import get_recent
from sudoisbot.common import init


def fmt_time(time):
    #return time.isoformat().split("T")[1][:5]
    return time

def read_data(fname, hours, sensor_count):

    # >>> len("2020-06-16T01:36:43,inside,22.18")
    # 45 # bytes
    # if theres one datapoint per minute over 24h
    # >>> 45 * 60 * 24
    # 46080 # bytes
    # which is
    # >>> 46080 // 1024
    # 45 # kb
    # so max 45 kb per sensor...

    now = datetime.now()
    per_sensor = defaultdict(list)
    okdiff = timedelta(hours=hours)
    with open(fname, 'r') as f:
        for datapoint in deque(f, 60*hours*sensor_count):
            dp = datapoint.strip()
            ts, name, value = dp.split(",")
            dt = datetime.fromisoformat(ts)
            age = now - dt
            if age < okdiff:
                per_sensor[name].append( (dt, float(value) ))
    return per_sensor

def remove_whacky(values):
    sane = list()
    last = values[0]
    for i in range(10):
        if abs(values[i]-values[i+1]) < 10:
            logger.debug(f"starting from {i}")
            start = i
            break
        elif i == 9:
            logger.error("list is whacky, exitign")
            raise SystemError("Whacky list")



    for value in values[start:]:
        if abs(value-last) > 10:
            logger.warning(f"replacing '{value}' with '{last}'")
            sane.append(last)
        else:
            sane.append(value)
    return sane



def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--data", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--hours", type=int, default=12)
    parser.add_argument("--interval", help="secs between readings", default=30)
    parser.add_argument("--name", required=True)

    config, args = init(__name__, parser, fullconfig=True)

    # this config file structure is a fucking nightmare
    recent_temps = get_recent(config['temper_sub']['state_file'],
                              grace=args.hours*60)


    data = read_data(args.data, args.hours, len(recent_temps))
    for sensor in data.keys():
        logger.info(f"{sensor}:")
        logger.info(f"start: {data[sensor][0][0]}")
        logger.info(f"end:   {data[sensor][-1][0]}")

    assert args.name in data.keys()
    logger.warning(f"plotting '{args.name}'")

    x_list, y_list_raw = zip(*data[args.name])
    y_list = remove_whacky(y_list_raw)

    x = numpy.array(x_list)
    y = numpy.array(y_list)

    fig, ax = plt.subplots()

    logger.debug("plotting..")
    plt.autumn()
    plt.plot(x, y)

    x_labels = ax.xaxis.get_ticklabels()
    for n, label in enumerate(x_labels[1:-1]):
        if n % 4 != 2:
            label.set_visible(False)

    plt.title(f"Temperature {args.hours}h ({args.name})")
    plt.ylabel("Celcius")
    plt.savefig(args.output_file)

    logger.info(f"wrote '{args.output_file}'")
