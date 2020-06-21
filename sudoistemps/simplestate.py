#!/usr/bin/env python3

import json
from datetime import datetime, timedelta

def get_recent(statefile, grace=10):
    state = get_state(statefile)
    now = datetime.now()
    okdiff = timedelta(minutes=grace)
    temps = dict()
    for name, values in state.items():
        dt = datetime.fromisoformat(values['timestamp'])
        if now - dt < okdiff:
            temps[name] = values
    if not any(temps.values()):
        raise ValueError("no recent temp data was found")
    else:
        return temps


def get_state(statename):
    try:
        with open(statename, 'r') as f:
            return json.loads(f.read())
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return dict()

def update_state(update, statename, key=""):
    state = get_state(statename)
    try:
        name = update['name']
        state[update['name']] = update
    except TypeError:
        state[key] = update
    with open(statename, 'w') as f:
        f.write(json.dumps(state, indent=4))
