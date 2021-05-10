#!/usr/bin/python3

import sys

from playhouse.migrate import *

from sudoisbot.config import read_config
from sudoisbot.sink.models import *

config = read_config(sys.argv[1])

db = dbconnect(**config['mysql'])
migrator = MySQLMigrator(db)

migrate(
    # migrator.add_index('temperatures', ('name',), False)
)
