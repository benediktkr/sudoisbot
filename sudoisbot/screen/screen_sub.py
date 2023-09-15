#!/usr/bin/python3 -u

# written for py3.5 because thats what was on the zero, and to be able
# to run stand-alone outside of the package, so its not relying on methods
# from sudoisbot.common, and uses print() for logging (meant to be sent to
# syslog with systemd). also uses a different config file and config
# system, just reading a simple json file.
#
# the idea is that its just supposed to be a dumb screen, and its currently
# not managed properly. but that might change at some point.

# https://github.com/pimoroni/inky-phat-redux
#
# sudo apt-get install python3-pip python3-dev
# pip3 install inky[rpi,fonts]

# also needs
# - python3-zmq
# - python3-pil
# - python3-dateutil
# - libatlas-base-dev


# if its not starting, try
# >>> import inkyphat
# in python3 shell

#
# written for the older inkyphat library that is installed
# with an annoying curlpipe
#
# curl https://get.pimoroni.com/inky | bash

# sudo mv screen_sub.json /etc
# sudo cp screen_sub.py /usr/local/sbin
# sudo mv screen_sub.systemd /etc/systemd/system/screen_sub.service
# sudo systemctl --system daemon-reload
# sudo systemctl enable screen_sub
# sudo systemctl start screen_sub


# Installing (done for reinstall)
# python3 -m venv ~/.cache/virtualenvs/eink
# source ~/.cache/virtualenvs/eink/bin/activate
# # the older library, not needed
# pip install inkyphat
# pip install "inky[rpi,fonts]"
#
# apt-get install libopenjp2-7
#
#
# user needs to be in the gpio and spi groups 
# $ ls -l /dev/gpiomem
# crw-rw---- 1 root gpio 246, 0 Sep 15 12:49 /dev/gpiomem
# ls -l /dev/spidev0.0
# crw-rw---- 1 root spi 153, 0 Sep 15 13:09 /dev/spidev0.0

import argparse
from datetime import datetime, timedelta, timezone
import json
from time import sleep
import sys

import dateutil.parser
import zmq
from loguru import logger

logger.remove()
logger.add("/dev/shm/screen_sub.log")

try:
    from PIL import ImageFont
    # import inkyphat
    # new
    from inky import InkyPHAT
    from PIL import Image, ImageDraw

    inky_display = InkyPHAT('black')

    have_inky = True
except ImportError:
    have_inky = False

def should_update(last_updated, min_update_interval, debug=False):
    if last_updated == False:
        return True

    now =  datetime.now(timezone.utc)
    age = now - last_updated
    next_ = min_update_interval - age.seconds

    if next_ <= 0:
        return True
    else:
        return False


def gettext(text, br=""):
    MAX_LINES = 7
    MAX_CHARS = 34
    have = len(text.strip().split('\n'))
    fillers = '\n'*(max(MAX_LINES - have, 0))
    timestamp = datetime.now().isoformat().replace("T", " ")[5:16]
    # doesnt handle too long messagse fix later
    body = text + fillers

    space_footer = MAX_CHARS-len(timestamp)
    footer = timestamp + br.rjust(space_footer - 1)
    return body + footer

def inky_write(text, rotation=0, br=''):
    text = gettext(text, br)
    if have_inky:
        return inky_write_eink(text, rotation)
    else:
        return inky_write_mock(text)

def inky_write_mock(text):
    print()
    print("  " + "-"*38)
    for i, line in enumerate(text.splitlines()):
        left = f"{i} | {line}"
        right = " | ".rjust(41-len(left))
        print(left+right)
    print("  " + "-"*38)
    print()

def inky_write_eink(text, rotation):
    inky_display.set_border(inky_display.RED)

    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
    xy = (0, 0)

    img = Image.new("P", inky_display.resolution)
    draw = ImageDraw.Draw(img)

    draw.text(xy, text, inky_display.BLACK, font=font)

    inky_display.set_image(img)
    lines = len([a for a in text.splitlines() if a != ""])
    sys.stdout.flush()
    inky_display.show()


def sub(addr, topic, timeout, debug):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, topic)
    socket.setsockopt(zmq.RCVTIMEO, timeout)

    socket.connect(addr)
    last_updated = False # wrong type :)

    #logger.info("Subscribed to: {}".format(addr))
    #logger.info("Topic: {}".format(topic))

    while True:
        # wait for updates
        try:
            msg = socket.recv_multipart()
        except zmq.error.Again:
            socket.close()
            context.destroy()
            raise

        j = json.loads(msg[1].decode())

        # minimum allowed unless forced. regulating updater intervals
        # is the responsiblity of screen_pub, this is just to prevent flooding
        # since refreshing the display takes a while, a flood would take
        # very long to process, and a suicide snail doesnt make much sense
        # since 2 min valid information is perfectly fine, and a forcedfor
        # update would bypass this anyway
        default_mui = 2*60
        mui = int(j.get('min_update_interval', default_mui))

        force_update = j.get('force_update', False) or not have_inky

        ts = datetime.strptime(j['timestamp'][:-6], "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)

        now =  datetime.now(timezone.utc)
        age = now - ts
        if age > timedelta(seconds=1.0):
            continue

        elif should_update(last_updated, mui, debug) or force_update:

            rotation = j.get("rotation", 0)
            inky_write(j['text'], rotation, br=j.get('bottom_right', ''))

            last_updated =  datetime.now(timezone.utc)

        else:
            pass

@logger.catch
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--addr")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--config", default="/etc/screen_sub.json")
    args = parser.parse_args()

    with open(args.config) as f:
        conf = json.load(f)

    #logfile = conf.get("logfile", "/tmp/screen_sub.log")
    #logger.add(logfile)

    if not args.addr:
        # this could do with some error handling probably
        addr = conf['addr']
    else:
        addr = args.addr

    inky_write("Starting.. waiting for update \nfrom {}..".format(addr))

    sleep(3.0)

    while True:
        # endless loop to handle reconnects
        try:
            sub(addr, b"eink", 1000*60*5, args.debug)
        except zmq.error.Again:
            inky_write("no messages, reconnecting \nto: {}".format(addr))
            continue
        except KeyboardInterrupt:
            inky_write("stopped")
            raise SystemExit

if __name__ == "__main__":
    main()
