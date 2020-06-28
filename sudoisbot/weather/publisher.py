#!/usr/bin/python3

# S21 msl: 40
# S21 lat long: (52.5167654, 13.4656278)
#

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

from datetime import datetime
from decimal import Decimal
import os
import pkg_resources
import time

import requests
from loguru import logger

from sudoisbot.network.pub import WeatherPublisher
from sudoisbot.common import init, catch

version = pkg_resources.get_distribution('sudoisbot').version
user_agent = f"sudoisbot/{version} github.com/benediktkr/sudoisbot"

#user_agent2 = f"{user_agent} schedule: 60m. this is a manual run for development, manually run by my author. hello to anyone reading, contact info on github"

lat_lon = ('52.5167654', '13.4656278')
lat, lon = map(Decimal, lat_lon)
msl = 40


owm_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat:.4f}&lon={lon:.4f}&appid={owm_token}&sea_level={msl}&units=metric"

def get_weather():

    import json
    logger.add("/tmp/owm_odd.json", format="{message}", filter=lambda x: 'odd' in x['extra'], level="TRACE")

    # needs refactoring do not check in like this
    s = requests.Session()
    s.headers.update({"User-Agent": user_agent,
                      "Accept": "application/json"})
    r = s.get(owm_url)
    # for met.no, check for 203, wont be raised
    r.raise_for_status()

    w = r.json()

    if len(w['weather']) > 1:
        logger.warning(f"got {len(w['weather'])} conditions")
        logger.warning(f"{w['weather']}")
        logger.bind(odd=True).trace(json.dumps(w))


    desc = ', '.join([a['description'] for a in w['weather']])
    main = ', '.join([a['main'] for a in w['weather']])
    temp = w['main']['temp']
    humid = w['main']['humidity']
    pressure = w['main']['pressure']
    wind = w['wind']
    rain = w.get('rain', {})
    if rain:  # test or True
        logger.warning(f"rain: '{rain}'")
    if "rain" in w:
        logger.warning(f"w.rain: '{w['rain']}'")
        logger.bind(odd=True).trace(json.dumps(w))
    snow = w.get('snow', {})
    if snow:
        logger.warning(f"snow: '{snow}'")
        logger.bind(odd=True).trace(json.dumps(w))
    dt = w['dt']
    # misnomer on my behalf
    # .fromtimestamp() -> converts to our tz (from UTC)
    # .utcfromtimestamp() -> returns in UTC
    weather_dt = datetime.fromtimestamp(dt).isoformat()

    raining = 'rain' in main.lower() or 'rain' in desc.lower() or bool(rain)
    snowing = 'snow' in main.lower() or 'snow' in desc.lower() or bool(snow)

    d = {
        'temp': temp,
        'humid': humid,
        'weather': {
            'temp': temp,
            'desc': desc,
            'humid': humid,
            'wind': wind,
            'rain': rain,
            'main': main,
            'snow': snow,
            'pressure': pressure,
            'precipitation': {
                'raining': raining,
                'snowing': snowing,
                'either': raining or snowing
            }
        }
    }

    return d



def pub(addr):
    freq = 60 * 5 # 5 mins

    publisher = WeatherPublisher(addr, "fhain", freq)
    #time.sleep(5.0) # bah
    #logger.debug("done sleeping")

    while True:
        weather = get_weather()
        publisher.send_weather(weather)

        time.sleep(freq)


@catch()
def main():
    config = init("weather_pub", fullconfig=True)
    addr = config['temper_pub']['addr']

    pub(addr)
