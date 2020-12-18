#!/usr/bin/python3 -u

# written for py3.5 because thats what was on the zero, and to be able
# to run stand-alone outside of the package, so its not relying on methods
# from sudoisbot.common, and uses print() for logging (meant to be sent to
# syslog with systemd). also uses a different config file and config
# system, just reading a simple json file.
#
# the idea is that its just supposed to be a dumb screen, and its currently
# not managed properly. but that might change at some point.

# sudo mv screen_sub.json /etc
# sudo cp screen_sub.py /usr/local/sbin
# sudo mv screen_sub.systemd /etc/systemd/system/screen_sub.service
# sudo systemctl --system daemon-reload
# sudo systemctl enable screen_sub
# sudo systemctl start screen_sub

import argparse
from datetime import datetime, timedelta, timezone
import json
from time import sleep

import dateutil.parser
import zmq

try:
    from PIL import ImageFont
    import inkyphat
    have_inky = True
except ImportError:
    have_inky = False

def log(text):
    if have_inky:
        # assuming systemd and syslog
        print(text)
    else:
        ts = datetime.now().isoformat()[5:19]
        s = "{}\t{}".format(ts, text)
        print(s)
        with open("/tmp/screen_sub.log", 'a') as f:
            f.write(s + "\n")

def should_update(last_updated, min_update_interval, debug=False):
    if last_updated == False:
        if debug:
           log("last_updated is False")
        return True

    now =  datetime.now(timezone.utc)
    age = now - last_updated
    next_ = min_update_interval - age.seconds

    if debug:
        if next_ > 0:
            log("next update in {} seconds".format(next_))
        else:
            log("pub forcing, last update was: {} sec ago".format(abs(next_)))

    if next_ <= 0:
        return True
    else:
        #log("next update in {} seconds".format(next))
        return False


def gettext(message):
    MAX_LINES = 8
    text = message['text']
    have = len(text.strip().split('\n'))
    fillers = '\n'*(max(MAX_LINES - have, 0))
    timestamp = datetime.now().isoformat().replace("T", " ")[5:16]
    bottom_right = message.get('bottom_right', '')
    # doesnt handle too long messagse fix later
    return text + fillers + timestamp + bottom_right



def inky_write(text, rotation=0, color='black'):
    if not have_inky:
        print(text)
        return
    inkyphat.set_colour(color)
    inkyphat.set_rotation(rotation)
    #inkyphat.set_border('black')
    #font = inkyphat.ImageFont.truetype(
    #    inkyphat.fonts.PressStart2P, 8)
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
    #font = ImageFont.truetype("/usr/share/fonts/basis33.ttf", 13)
    xy = (0, 0)
    if color == "red":
        fill = inkyphat.RED
    else:
        fill = inkyphat.BLACK
    inkyphat.clear()
    inkyphat.text(xy, text, fill=fill, font=font)
    inkyphat.show()


def sub(addr, topic, timeout, debug):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, topic)
    socket.setsockopt(zmq.RCVTIMEO, timeout)

    socket.connect(addr)
    last_updated = False # wrong type :)

    log("Subscribed to: {}".format(addr))
    log("Topic: {}".format(topic))

    while True:
        # wait for updates
        try:
            msg = socket.recv_multipart()
        except zmq.error.Again:
            log("timed out after {} seconds".format(timeout // 1000))
            socket.close()
            context.destroy()
            raise

        j = json.loads(msg[1].decode())

        # minimum allowed unless forced. regulating updater intervals
        # is the responsiblity of screen_pub, this is just to prevent flooding
        # since refreshing the display takes a while, a flood would take
        # very long to process, and a suicide snail doesnt make much sense
        # since 2 min valid information is perfectly fine, and a forced
        # update would bypass this anyway
        default_mui = 2*60
        mui = int(j.get('min_update_interval', default_mui))

        if debug:
            log("received: " + repr(msg[1].decode()))
            log("mui: {}".format(mui))

        force_update = j.get('force_update', False)
        color = j.get('color', 'black')

        # TBB: discard flood messages

        ts = datetime.strptime(j['timestamp'][:-6], "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)

        now =  datetime.now(timezone.utc)
        if ts - now > timedelta(seconds=1.0):
            log("discarding old message: '{}'".format(j['timestamp']))

        elif should_update(last_updated, mui, debug) or force_update:
            if mui == 0 or force_update:
                log("starting forced update")
            if not have_inky:
                log("would update e-ink display")
            rotation = j.get("rotation", 0)
            text = gettext(j)
            inky_write(text, rotation, color)
            if have_inky:
                log("e-ink screen updated")
            last_updated =  datetime.now(timezone.utc)

        else:
            pass

def zmq_tg(addr):
    tgcontext = zmq.Context()
    tgsock = tgcontext.socket(zmq.REQ)
    tgsock.connect(addr)
    log("connected to zmq req socket for tg on {}".format(addr))
    return tgsock

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--addr")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    with open("/etc/screen_sub.json") as f:
        conf = json.load(f)

    if not args.addr:
        # this could do with some error handling probably
        addr = conf['addr']
    else:
        addr = args.addr

    log("Have inky: {}".format(have_inky))
    inky_write("Starting.. waiting for update \nfrom {}..".format(addr))

    sleep(3.0)

    while True:
        # endless loop to handle reconnects
        try:
            sub(addr, b"eink", 1000*60*5, args.debug)
        except zmq.error.Again:
            inky_write("no messages, reconnecting \nto: {}".format(addr))
            log("reconnecting to {}".format(addr))
            continue
        except KeyboardInterrupt:
            inky_write("stopped")
            raise SystemExit
