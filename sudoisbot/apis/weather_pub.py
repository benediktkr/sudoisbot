#!/usr/bin/python3

# met.no:
#
# tuncate lat/long to 4 decimals
#
# Reponse headers (firefox):
#
# Date	Thu, 25 Jun 2020 20:55:23 GMT
# Expires	Thu, 25 Jun 2020 21:26:39 GMT
#
# Seems like 30 mins, but check "Expires"
#
# Use "If-Modified-Since" request header
#
# Depending on how i do this, add a random number of mins/secs to
# not do it on the hour/minute
#
# must support redirects and gzip compression (Accept-Encoding: gzip, deflate)
#

# openweatherap:
#
#
# triggers: https://openweathermap.org/triggers
#  - polling
#  - may as well poll nowcast
#
# ratelimit: 60 calls/minute
#
# weather condition codes: https://openweathermap.org/weather-conditions#Weather-Condition-Codes-2
#
# maybe interesting project: https://github.com/aceisace/Inky-Calendar

from datetime import datetime, timezone
from decimal import Decimal
import time
import json

import requests
from loguru import logger
from requests.exceptions import RequestException

from sudoisbot.network.pub import Publisher
from sudoisbot.config import read_config


# rain_conditions = [
#     'rain',
#     'drizzle',
#     'thunderstorm'
# ]

#         # raining = 'rain' in main.lower() or 'rain' in desc.lower()
#         # snowing = 'snow' in main.lower() or 'snow' in desc.lower()
#         # drizzling = 'drizzle' in main.lower() or 'drizzle' in desc.lower()
#         # thunderstorm = 'thunderstorm' in main.lower() or 'thunderstorm' in desc.lower()
#         # any_percip = raining or snowing or drizzling or thunderstorm
#         # if any_percip:
#         #     logger.bind(odd=True).trace(json.dumps(w))
#         # precipitation = {
#         #     'raining': raining,
#         #     'snowing': snowing,
#         #     'drizzling': drizzling,
#         #     'thunderstorm': thunderstorm,
#         #     'any': any_percip
#         # }

def useragent():
    import pkg_resources
    version = pkg_resources.get_distribution('sudoisbot').version
    return f"sudoisbot/{version} github.com/benediktkr/sudoisbot"



OWM_URL = "https://api.openweathermap.org/data/2.5/weather?lat={lat:.4f}&lon={lon:.4f}&appid={token}&sea_level={msl}&units=metric"


class NowcastPublisher(Publisher):

    def __init__(self, addr, locations, token, frequency):
        super().__init__(addr, b"weather", None, frequency)

        self.locations = [{
            'name': a['name'],
            'lat': Decimal(a['lat']),
            'lon': Decimal(a['lon']),
            'msl': a['msl']
            } for a in locations]


        self.token = token
        self.base_url = OWM_URL

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": useragent(),
                                     "Accept": "application/json"})

    def get_nowcast(self, location):
        url = self.base_url.format(token=self.token, **location)
        r = self.session.get(url)
        r.raise_for_status()
        if r.status_code == 203:
            logger.warning("deprecation warning: http 203 returned")

        w = r.json()

        d = dict(
            desc = ', '.join([a['description'] for a in w['weather']]),
            main = ', '.join([a['main'] for a in w['weather']]),

            temp = float(w['main']['temp']),
            feel_like = float(w['main']['feels_like']),
            pressure = float(w['main']['pressure']),
            humidity = float(w['main']['humidity']),

            wind_speed = float(w['wind'].get('speed', 0.0)),
            wind_deg = float(w['wind'].get('deg', 0.0)),

            visibility = w['visibility'],
            cloudiness = w['clouds']['all'],

            dt = w['dt'],
            # misnomer on my behalf
            # .fromtimestamp() -> converts to our tz (from UTC)
            # .utcfromtimestamp() -> returns in UTC
            weather_dt = datetime.fromtimestamp(w['dt']).isoformat()
        )


        #  only in the data when it's been raining/showing
        if 'rain' in w:
            rain_1h = w['rain'].get('1h'),
            rain_3h = w['rain'].get('3h'),
        if 'snow' in w:
            snow_1h = w['snow'].get('1h'),
            snow_3h = w['snow'].get('3h'),


        return d

    def publish(self):
        try:
            for location in self.locations:
                nowcast = self.get_nowcast(location)
                self.send(location['name'], nowcast)
                time.sleep(0.2)
        except RequestException as e:
            logger.error(e)

    def send(self, name, weather):
        now =  datetime.now(timezone.utc).isoformat()
        tags = {
            'name': name,
            'frequency': self.frequency,
            'type': 'weather',
            'kind': 'weather',
            'source': 'api',
            'environment': 'outside',
            'location': name,
        }
        data = {
            'measurement': self.topic.decode(),
            'tags': tags,
            'time': now,
            'fields': weather
        }
        # for legacy and consistency reasons
        for measurement in ['temp', 'humidity']:
            data2 = {
                'measurement': measurement,
                'tags': tags,
                'time': now,
                'fields': {'value': weather[measurement] }
            }
            jdata = json.dumps(data2)
            self.socket.send_multipart([b'temp', jdata.encode()])


        #bytedata = json.dumps(data).encode()
        #logger.debug(bytedata)
        #self.socket.send_multipart([self.topic, bytedata])
        msg = self.pub(data)
        logger.trace(msg)


def main(config):

    addr = config['addr']
    locations = config['locations']
    token = config['owm_token']
    freq = config['frequency']

    with NowcastPublisher(addr, locations, token, freq) as publisher:
        publisher.loop()
