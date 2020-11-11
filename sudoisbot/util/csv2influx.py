#!/usr/bin/python3
import sys
import argparse
from datetime import datetime
import os
import json
import dateutil.parser
from datetime import timezone
import fileinput

from loguru import logger
#from influxdb import InfluxDBClient
import requests.exceptions

#from sudoisbot.sink import models
from sudoisbot.sink.sink import ZFluxClient
from sudoisbot.config import read_config
from sudoisbot.common import init



def mkbody(dt, name, temp):
    dt = dateutil.parser.parse(dt).astimezone(timezone.utc).isoformat()
    return  {
        "measurement": "temp",
        "tags": {
            "name": name

        },
        "time": dt,
        "fields": {
            "value": float(f"{float(temp):.2f}") # ugh......
        }
    }



if __name__ == "__main__":
    config = read_config()
    zflux = ZFluxClient(topic=config['zflux']['topic'])
    zflux.connect(config['zflux']['addr'])


    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--csv")
    parser.add_argument("--last", type=int)
    args = parser.parse_args()

    # -csv /srv/temps/temps.csv --last 9500 &&

    #config, args = init("csv2influx", parser, fullconfig=True)

    #print(os.environ['GRAFANAPASS'])

    # logger.info("creating influxdb client")
    # client = InfluxDBClient(
    #     host='ingest.sudo.is',
    #     port=443,
    #     username='sudoisbot',
    #     password=os.environ['GRAFANAPASS'],
    #     ssl=True,
    #     verify_ssl=True,
    #     database='sudoisbot'
    # )

    if not args.csv:
        logger.info("waiting for stdin data")
        try:
            for line in fileinput.input():
                text = line.strip()
                dt, name, temp = text.split(",")
                body = mkbody(dt, name, temp)
                try:
                    zflux.send(body)
                    print(json.dumps(body))
                    # socket.gaierror: [Errno -2] Name or service not known
                    # urllib3.exceptions.NewConnectionError
                    # urllib3.exceptions.MaxRetryError: HTTPSConnectionPool
                    # requests.exceptions.ConnectionError: HTTPSConnectionPool(host='ingest.sudo.is',
                    # port=443): Max retries exceeded with url: /write?db=sudoisbot&precision=m (Cause
                    # d by NewConnectionError('<urllib3.connection.HTTPSConnection object at 0xb56a243
                    # 0>: Failed to establish a new connection: [Errno -2] Name or service not known'))

                    # 20.09.2020
                    # influxdb.exceptions.InfluxDBServerError: b'<html>\r\n<head><title>504 Gateway Time-out</title></head>\r\n<body>\r\n<center><h1>504 Gateway Time-out</h1></center>\r\n<hr><center>nginx/1.18.0 (Ubuntu)</center>\r\n</body>\r\n</html>\r\n'
                except requests.exceptions.ConnectionError as e:
                    raise SystemExit(f"fatal error: {e}")


        except KeyboardInterrupt:
            logger.info("ok ok im leaving!")
            raise SystemExit



    import time
    time.sleep(3.0)
    logger.info('done sleeping')

    l = list()
    name_input = ""
    logger.info(f"reading {args.csv}...")
    with open(args.csv, 'r') as f:
        for line in f.readlines():
            d = dict()
            items = line.strip().split(",")
            if len(items) == 2:
                # before i was smart enough to log the name
                if not name_input:
                    name_input = input("enter name: ")
                dt, d['temp'] = items
                d['name'] = name_input

            else:
                dt, name, temp = items
                d['name'], d['temp'] = name, temp

            #d['timestamp'] = datetime.fromisoformat(dt)
            d['timestamp'] = dt
            body = mkbody(dt, name, temp)
            # import json
            # print(json.dumps(body, indent=2))
            # raise SystemExit
            l.append(body)
    logger.info("finished reading file")


    # send to influx
    logger.info("sending to zflux")
    if args.last:
        sendthis = l[-args.last:]
        logger.info(f"just sending last {args.last} measurements")
        #client.write_points(sendthis, batch_size=100, time_precision='m')
        for item in sendthis:
            zflux.send(item)
        print(json.dumps(sendthis[0], indent=2))
        print(json.dumps(sendthis[-1], indent=2))
        #print(len([a for a in sendthis if a['tags']['name'] == 'bedroom']))


    else:
        raise NotImplementedError
        #logger.info("sending all measurements from csv file")
        #client.write_points(l, batch_size=100, time_precision='m')


    #             try:
    #                 record = models.Temps.create(**d)
    #                 imported.append(record)
    #             except IntegrityError as e:
    #                 if e.args[0].startswith("UNIQUE"):
    #                     dups.append(line)
    #                     if not args.ignore_dup:
    #                         # still ignore them per say, put still print
    #                         # a warning if we're not expecting them
    #                         logger.warning(f"{e}: '{line}'")
    #                 else:
    #                     logger.error(e)
    # logger.info(f"duplicates: {len(dups)}")
    # logger.info(f"imported {len(imported)} rows from '{args.csv}'")
    # logger.info(f"database: '{args.db}'")
    # logger.info(f"from: {imported[0].timestamp}")
    # logger.info(f"to: {imported[-1].timestamp}")
