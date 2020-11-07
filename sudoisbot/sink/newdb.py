#!/usr/bin/python3

import sys
import os
from sudoisbot.sink import models

sqlitefile = sys.argv[1]

if os.path.exists(sqlitefile):
    raise SystemExit(f"file '{sqlitefile}' exists, not doing anything")


models.create_tables("sqlite:///" + sqlitefile)
