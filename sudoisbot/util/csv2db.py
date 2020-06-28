#!/usr/bin/python3

'''
[ben@pi1 sudoisbot (master ✗)]$ history | cut -c 8- | grep csv2db | sort -u

csv2db.py --csv firstlog.csv --db "sqlite:///db.sqlite"  --ignore-dup
csv2db.py --csv fromlog.csv --db "sqlite:///db.sqlite"  --ignore-dup
csv2db.py --csv /srv/temps/temps.csv --db "sqlite:///db.sqlite"
csv2db.py --csv /srv/temps/temps.csv --db "sqlite:///db.sqlite"  --ignore-dup
csv2db.py /srv/temps/temps.csv db.sqlite
'''

# /srv/temps/temps.csv: 15418 (inside, fhain)
# /srv/temper_sub.inside.csv 4 (inside)
# fromlog.csv, 26 (inside + fhain, awk from loguru log, s/outside/fhain)
# hh19.csv, 11860 (hh19)
# inside.firstlog.log, 85114 (inside)

#   inside.firstlog.csv is every 1 mins 2020-04-17 to 2020-06-16
# temper_sub.inside.csv is every 4 mins 2020-05-10 to 2020-06-21
#
# so inside.firstlog.csv will overlap temper_sub.inside.csv until
# it ends on 2020-06-16 becuase they didnt run on exactly the same
# time:
#
#   sqlite> select timestamp, temp from temps
#      ...> where timestamp > "2020-06-10 14:45"
#      ...> AND timestamp < "2020-06-10 14:47";
#   2020-06-10 14:45:01|23.5
#   2020-06-10 14:46:01|23.5
#   2020-06-10 14:46:55|24.31
#
# so there are records of the same minute sometimes. havent
# deleted them since i dont know which one is more/less accurate
#
# imported in this order:
#              hh19.csv: 2020-04-09 to 2020-04-17, 11860 rows, hh19
#   inside.firstlog.csv: 2020-04-17 to 2020-06-16, 85380 rows, inside
# temper_sub.inside.csv: 2020-05-10 to 2020-06-21, 13419 rows, inside
#  /srv/temps/temps.csv: 2020-06-21 to 2020-06-26, 1827 rows, inside+fhai
#
#
# $ du -sh db.sqlite
# 13M     db.sqlite
#
# importing a smaller subset of 40 days, one sensor with 4 min readings
# $ du -sh db.sqlite
# 1.6M    db.sqlite
#
# then
# >>> 1.6/40 * 365
# 14.6
#
# so 14.6 mb per sensor with 4 min readings

import sys
import argparse
from datetime import datetime

from loguru import logger
from playhouse.db_url import connect
from peewee import IntegrityError

from sudoisbot.sink import models
from sudoisbot.common import init

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--csv", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--ignore-dup", action="store_true")

    config, args = init("csv2db", parser, fullconfig=True)

    db = connect(args.db)
    models.db.initialize(db)
    #models.Temps.bind(db)

    imported = list()
    dups = list()

    name_input = ""

    with models.db:
        with open(args.csv, 'r') as f:
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
                    dt, d['name'], d['temp'] = items

                d['timestamp'] = datetime.fromisoformat(dt)

                try:
                    record = models.Temps.create(**d)
                    imported.append(record)
                except IntegrityError as e:
                    if e.args[0].startswith("UNIQUE"):
                        dups.append(line)
                        if not args.ignore_dup:
                            # still ignore them per say, put still print
                            # a warning if we're not expecting them
                            logger.warning(f"{e}: '{line}'")
                    else:
                        logger.error(e)
    logger.info(f"duplicates: {len(dups)}")
    logger.info(f"imported {len(imported)} rows from '{args.csv}'")
    logger.info(f"from: {imported[0].timestamp}")
    logger.info(f"to: {imported[-1].timestamp}")
