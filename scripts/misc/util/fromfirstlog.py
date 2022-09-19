#!/usr/bin/python3

"""
[ben@pi1 sudoisbot (master ✗)]$ stat /srv/temper_sub.inside.csv
  File: /srv/temper_sub.inside.csv
  Size: 384532          Blocks: 760        IO Block: 4096   regular file
Device: b302h/45826d    Inode: 6294        Links: 1
Access: (0644/-rw-r--r--)  Uid: (    0/    root)   Gid: (    0/    root)
Access: 2020-05-10 16:33:26.589967470 +0200
Modify: 2020-06-21 14:59:30.770452264 +0200
Change: 2020-06-21 14:59:30.770452264 +0200
 Birth: -
"""

"""
[ben@pi1 sudoisbot (master ✗)]$ stat /srv/temps.txt
  File: /srv/temps.txt
  Size: 501667          Blocks: 992        IO Block: 4096   regular file
Device: b302h/45826d    Inode: 1448        Links: 1
Access: (0644/-rw-r--r--)  Uid: (    0/    root)   Gid: (    0/    root)
Access: 2020-04-17 12:21:35.369999836 +0200
Modify: 2020-06-15 22:17:01.777403702 +0200
Change: 2020-06-15 22:17:01.777403702 +0200
 Birth: -
"""

"""
[ben@pi1 sudoisbot (master ✗)]$ stat /srv/hh19-temps.txt
  File: /srv/hh19-temps.txt
  Size: 66428           Blocks: 144        IO Block: 4096   regular file
Device: b302h/45826d    Inode: 1688        Links: 1
Access: (0644/-rw-r--r--)  Uid: (    0/    root)   Gid: (    0/    root)
Access: 2020-04-10 01:00:31.727601510 +0200
Modify: 2020-04-17 12:20:01.879999892 +0200
Change: 2020-04-17 12:20:24.369999878 +0200
 Birth: -
"""


"""
[ben@pi1 sudoisbot (master ✗)]$ poetry run python3 sudoistemps/fromfirstlog.py ~/tmp/hh19-temps.txt hh19.csv
file last modified at: 2020-04-17 14:20:01.880000
using name: hh19
             oldest: 2020-04-09T08:41:01,hh19,24.31
last entry is from : 2020-04-17T14:20:01,hh19,24.31
             random: 2020-04-16T09:05:01,hh19,21.5
wrote 11860 lines to hh19.csv
"""

"""
[ben@pi1 sudoisbot (master ✗)]$ poetry run python3 sudoistemps/fromfirstlog.py ~/tmp/temps.txt inside.firstlog.csv
file last modified at: 2020-06-16 00:17:01.777404
using name: inside
            oldest: 2020-04-17T17:18:01,inside,24.31
last entry is from: 2020-06-16T00:17:01,inside,24.31
            random: 2020-06-11T22:13:01,inside,24.31
wrote 85380 lines to inside.firstlog.csv
"""

from datetime import datetime, timedelta
import os
import sys

#last_utc_string = "2020-06-21 14:59:30.770452264 +0200"
#last_iso_utc = "2020-06-21T14:59:30.770452+02:00"
#last_iso = "2020-06-21T16:59:30.770452"

#last_utc_string = "2020-06-15 22:17:01.777403702 +0200"
#last_iso_utc = "2020-06-15T22:17:01.777403+02:00"
#last_iso = "2020-06-16T00:17:01.777403"

fname = sys.argv[1]
mtime = os.stat(fname).st_mtime
last_utc = datetime.fromtimestamp(mtime)
last = last_utc + timedelta(hours=2)

print(f"file last modified at: {last}")

#name = input("name: ")
name = sys.argv[2].split(".")[0]
print(f"using name: {name}")

with open(fname, 'r') as f:
    lines = f.readlines()

temps = reversed(lines)


freq = 60 # seconds

csv = list()

for i, item in enumerate(temps):
    dt = last - timedelta(seconds=freq*i)
    timestamp = dt.isoformat()[:19]
    if item.startswith("\x00"):
        item = item.strip('\x00')

    csvitem = f"{timestamp},{name},{item.strip()}"
    csv.append(csvitem)

print(f"            oldest: {csv[-1]}")
print(f"last entry is from: {csv[0]}")

import random
print(f"            random: {random.choice(csv)}")


with open(sys.argv[2], 'w') as f:
    for item in reversed(csv):
        f.write(item + "\n")

print(f"wrote {len(csv)} lines to {sys.argv[2]}")
