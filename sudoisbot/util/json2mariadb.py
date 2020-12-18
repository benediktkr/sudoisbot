#!/usr/bin/python3
import sys
import argparse
from datetime import datetime
import os
import json
import dateutil.parser
from datetime import timezone
import fileinput

from peewee import IntegrityError
from loguru import logger
import requests.exceptions

#from sudoisbot.sink import models
from sudoisbot.config import read_config
from sudoisbot.sink.models import Temperatures, Humidities, dbconnect

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("json")
    parser.add_argument("--config")
    parser.add_argument("--ignore-dups")
    args = parser.parse_args()

    config = read_config(args.config)
    db = dbconnect(**config['mysql'])

    temp_count = Temperatures.select().count()
    humi_count = Humidities.select().count()
    logger.info(f"temp count: {temp_count}")
    logger.info(f"humi count: {humi_count}")

    with open(args.json, 'r') as j:
        for line in j.readlines():
            msg = json.loads(line)
            msg['tags'].setdefault('location', 'unknown')
            try:
                if msg['measurement'] == "temp":
                    Temperatures.insert_msg(msg)
                elif msg['measurement'] == "humidity":
                    Humidities.insert_msg(msg)
            except IntegrityError as e:
                if e.args[1].startswith("Duplicate") and args.ignore_dups:
                    name = msg['tags']['name']
                    time = msg['time']
                    logger.info(f"ignoring from {name} on {time}")
                    pass
                else:
                    raise

    temp_count = Temperatures.select().count()
    humi_count = Humidities.select().count()
    logger.success(f"temp count: {temp_count}")
    logger.success(f"humi count: {humi_count}")
