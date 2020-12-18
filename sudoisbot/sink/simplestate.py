#!/usr/bin/env python3

import json
from datetime import datetime, timedelta, timezone

from loguru import logger

import sudoisbot.datatypes

def get_recent(statefile, grace=10):

    state = get_state(statefile)

    now =  datetime.now(timezone.utc)
    temps = dict()
    for name, data in state.items():
        okdiff = timedelta(minutes=grace, seconds=int(data['tags'].get('frequency', 240)))
        dt = datetime.fromisoformat(data['time'])

        try:
            diff = now - dt
            is_recent = diff < okdiff
        except TypeError as e:
            if "offset-naive and offset-aware" in e.args[0]:
                logger.warning(f"record for '{name}' doesnt have a tz")
                continue
            else:
                raise

        if is_recent:
            logger.trace(f"age of '{name}' state: {diff}")
            temps[name] = data
        else:
            logger.warning(f"record for '{name}' is too old (diff {diff})")
    if not any(temps.values()):
        raise ValueError("no recent temp data was found")
    else:
        return temps


def get_state(statename):
    race = False
    for _ in range(10):
        try:
            # reason to move this to sqlite:
            # when a process is writing this and another is reading
            # the file can be incomplete
            with open(statename, 'r') as f:
                text = f.read()
                return json.loads(text)

        except FileNotFoundError:
            if race:
                import time
                logger.warning(f"possible race condition: '{e}'")
                time.sleep(1.0)
            return dict()
        except json.decoder.JSONDecodeError as e:
            # corrupt file, probably because we ran into a race
            # condition with another proess and havent moved this
            # to a database yet
            import time
            race = True
            logger.warning(f"possible race condition: '{e}'")
            time.sleep(1.0)


def update_state(updatemsg, statefilename, key=""):
    if isinstance(updatemsg, sudoisbot.datatypes.Message):
        logger.warning("i sholdnt be called often and should be removed if this hacking session is fruitful")
        updatemsg = updatemsg.as_dict()

    name = updatemsg['tags']['name']
    state = get_state(statefilename)

    try:
        state[name].update(updatemsg)
    except KeyError:
        logger.info(f"adding '{name}' to state {statefilename}")
        state[name] = updatemsg

    with open(statefilename, 'w') as f:
        f.write(json.dumps(state, indent=4))
