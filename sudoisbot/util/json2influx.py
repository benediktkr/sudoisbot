#!/usr/bin/python3
import argparse
import json
from time import sleep

from loguru import logger

from sudoisbot.sink.sink import ZFluxClient
from sudoisbot.config import read_config


if __name__ == "__main__":
    config = read_config('/usr/local/etc/sudoisbot-sink.yml')

    parser = argparse.ArgumentParser()
    parser.add_argument("--json-file", required=True)
    parser.add_argument("--last", type=int)
    args = parser.parse_args()

    zflux = ZFluxClient(topic=config['zflux']['topic'])
    zflux.connect(config['zflux']['addr'])

    logger.info(f"reading {args.json_file}...")
    l = list()
    with open(args.json_file, 'r') as f:
        for line in f.readlines():
            jline = json.loads(line)
            l.append(jline)

    if args.last:
        sendthis = l[-args.last:]
    else:
        sendthis = l

    logger.info(f"read: {len(l)}, sending: {len(sendthis)}")


    logger.info("sleeping to avoid the late joiner syndrome")
    sleep(1.0)
    for item in sendthis:
        tochange = [k for k, v in item['fields'].items() if isinstance(v, int)]
        if tochange:
            n = item['tags']['name']
            m = item['measurement']
            for k in tochange:
                logger.warning(f"field: '{k}', measurement: {m}, name: {n} to float")
        tosend = {
            'measurement': item['measurement'],
            'fields': {
                k: float(v) if isinstance(v, int) else v
                for k, v in item['fields'].items()
            },
            'tags': item['tags'],
            'time': item['time'],
        }
        zflux.send(tosend)

    print(f"oldets sent: {sendthis[0]['time']}")
    print(f"newestsent: {sendthis[-1]['time']}")
