#!/usr/bin/python3

import sys
import os
from sudoistemps import sink

sqlitefile = sys.argv[1]

if os.path.exists(sqlitefile):
    raise SystemExit(f"file '{sqlitefile}' exists, not doing anything")


sink.create_tables("sqlite:///" + sqlitefile)
