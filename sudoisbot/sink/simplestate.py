#!/usr/bin/env python3

import json
from datetime import datetime, timedelta

from loguru import logger

def get_recent(statefile, grace=10):
    state = get_state(statefile)
    now = datetime.now()
    temps = dict()
    for name, values in state.items():
        okdiff = timedelta(minutes=grace, seconds=int(values['frequency']))
        dt = datetime.fromisoformat(values['timestamp'])
        if now - dt < okdiff:
            temps[name] = values
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

def update_state(update, statename, key=""):
    state = get_state(statename)
    try:
        name = update['name']
        state[update['name']] = update
    except TypeError:
        state[key] = update
    with open(statename, 'w') as f:
        f.write(json.dumps(state, indent=4))
