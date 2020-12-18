#!/usr/bin/python3
import sys
import argparse
from datetime import datetime
import os
import json
import dateutil.parser
from datetime import timezone
import fileinput

from loguru import logger
import requests.exceptions

#from sudoisbot.sink import models
from sudoisbot.config import read_config



if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("csv")
    parser.add_argument("json")
    parser.add_argument("--state")
    args = parser.parse_args()

    with open(args.state, 'r') as f:
        state = json.load(f)

    def mktags(name):
        if name == "inside":
            return {
                'name': name,
                'environment': 'inside',
                'kind': 'temper',
                'source': 'sensor',
                'frequency': 240
            }

        else:
            tags = state[name]['tags']
            tags['frequency'] = 240
            return tags


    def mkjson(dt, name, temp):
        dt = dateutil.parser.parse(dt).astimezone(timezone.utc).isoformat()
        return json.dumps({
            "measurement": "temp",
            "tags": mktags(name),
            "time": dt,
            "fields": {
                "value": float(f"{float(temp):.2f}") # ugh......
            }
        })



    name_input = ""
    with open(args.csv, 'r') as f:
        with open(args.json, 'w') as j:
            for line in f.readlines():
                d = dict()
                items = line.strip().split(",")
                if len(items) == 2:
                    # before i was smart enough to log the name
                    if not name_input:
                        name_input = input("enter name: ")
                    dt, d['temp'] = items
                    d['name'] = name_input

                else:
                    dt, name, temp = items
                    d['name'], d['temp'] = name, temp

                #d['timestamp'] = datetime.fromisoformat(dt)
                d['timestamp'] = dt

                j.write(mkjson(dt, name, temp))
                j.write("\n")
