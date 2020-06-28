#!/usr/bin/env python3

from collections import deque, defaultdict
import argparse
import sys
import os
from datetime import datetime, timedelta
from math import ceil

import matplotlib.pyplot as plt
import numpy
from loguru import logger

from sudoisbot.sink.simplestate import get_recent
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
                per_sensor[name].append( (dt, float(value)) )
    return per_sensor

def clean_whacky(values):
    sane = list()
    last = values[0]
    for i in range(10):
        if abs(values[i]-values[i+1]) < 10:
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
            last = value
            sane.append(value)
    return sane


def graph(name, filename, hours, outputfile, count):
    data = read_data(filename, hours, count)
    return make_graph(name, data[name], outputfile)

def make_graph(name, data, outputfile, hours=""):

    # TODO: handle edge case if data is empty

    logger.debug(f"{name} start: {data[0][0]}")
    logger.debug(f"{name} end:   {data[-1][0]}")

    delta = data[-1][0] - data[0][0]
    delta_h = ceil(delta.seconds / 3600)

    x_list, y_list_raw = zip(*data)
    y_list = clean_whacky(y_list_raw)

    x = numpy.array(x_list)
    y = numpy.array(y_list)

    logger.warning(len(x_list))

    fig, ax = plt.subplots()

    plt.autumn()
    plt.plot(x, y)

    x_labels = ax.xaxis.get_ticklabels()
    for n, label in enumerate(x_labels[1:-1]):
        if n % 4 != 2:
            label.set_visible(False)

    plt.title(f"Temperature {delta_h}h ({name})")
    plt.ylabel("Celcius")

    plt.savefig(outputfile, format="png")
    logger.info(f"plotted '{name}' ({delta_h}h)")
    if isinstance(outputfile, str):
        logger.info(f"wrote '{outputfile}'")

    return len(data)



def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--data", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--hours", type=int, default=24)

    config, args = init(__name__, parser, fullconfig=True)

    # this config file structure is a fucking nightmare
    recent_temps = get_recent(config['temper_sub']['state_file'],
                              grace=args.hours*60 + 120)
    count = len(recent_temps)
    logger.debug(f"found {count} recent measurements")


    # data = read_data(args.data, args.hours, count)
    # out = os.path.join(args.output_dir, f"plot-{args.hours}.png")
    # make_graph(recent_temps.keys(), data, out, args.hours)

    for name in recent_temps.keys():
        data = read_data(args.data, args.hours, count)
        out = os.path.join(args.output_dir, f"{name}-{args.hours}.png")
        make_graph(name, data[name], out)
