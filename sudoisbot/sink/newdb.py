#!/usr/bin/python3

import sys
import os
from peewee import MySQLDatabase, ProgrammingError
from loguru import logger
from sudoisbot.sink import models
from sudoisbot.config import read_config

conf_file = sys.argv[1]

config = read_config(conf_file)

with MySQLDatabase(**config['mysql']) as db:
    models.db_proxy.initialize(db)

    should_exist = [models.Temperatures, models.Humidities]
    create = []
    for table in should_exist:
        try:
            count = table.select().count()
            if count > 0:
                logger.info(f"{table} table has {count} rows, ignoring")
                continue
        except ProgrammingError as e:
            if not e.args[1].endswith("doesn't exist"):
                raise

        create.append(table)

    if len(create) > 0:
        db.create_tables(create)
        logger.info(f"created {create}")
    else:
        logger.warning("did nothing")
