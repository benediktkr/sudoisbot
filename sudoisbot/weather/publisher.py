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
import time
import json

import requests
from loguru import logger

from sudoisbot.network.pub import Publisher
from sudoisbot.common import init, catch, useragent


#user_agent2 = f"{user_agent} schedule: 60m. this is a manual run for development, manually run by my author. hello to anyone reading, contact info on github"

lat_lon = ('52.5167654', '13.4656278')
lat, lon = map(Decimal, lat_lon)
msl = 40


owm_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat:.4f}&lon={lon:.4f}&appid={owm_token}&sea_level={msl}&units=metric"

rain_conditions = [
    'rain',
    'drizzle',
    'thunderstorm'
]

class NowcastPublisher(Publisher):

    def __init__(self, addr, name, freq, location, msl, config):
        super().__init__(addr, "temp", name, freq)
        self.type = "weather"
        self.lat, self.lon = map(Decimal, location)
        #self.token = config['token']
        #self.url = config['url']
        self.token = owm_token
        self.url = owm_url.format(lat=self.lat, lon=self.lon)

        logger.debug(self.url)

        # for debugging and understanding the data
        logger.add("/tmp/owm_odd.json",
                   format="{message}",
                   filter=lambda x: 'odd' in x['extra'], level="TRACE")


        self.session = requests.Session()
        self.session.headers.update({"User-Agent": useragent(),
                                     "Accept": "application/json"})

    # def message(self, weather):
    #     super().message()

    def send(self, weather):
        data = self.message()
        data['weather'] = weather
        data['temp'] = weather['temp']
        data['humidity'] = weather['humidity']
        sdata = json.dumps(data)
        # parent class has debug logger
        self.send_string(sdata)

    def query_api(self):
        r = self.session.get(self.url)
        r.raise_for_status()
        if r.status_code == 203:
            logger.warning("deprecation warning: http 203 returned")
        return r.json()

    def get_nowcast(self):
        w = self.query_api()


        if len(w['weather']) > 1:
            logger.warning(f"got {len(w['weather'])} conditions")
            logger.warning(f"{w['weather']}")
            logger.bind(odd=True).trace(json.dumps(w))

        desc = ', '.join([a['description'] for a in w['weather']])
        main = ', '.join([a['main'] for a in w['weather']])


        raining = 'rain' in main.lower() or 'rain' in desc.lower()
        snowing = 'snow' in main.lower() or 'snow' in desc.lower()
        drizzling = 'drizzle' in main.lower() or 'drizzle' in desc.lower()
        thunderstorm = 'thunderstorm' in main.lower() or 'thunderstorm' in desc.lower()
        any_percip = raining or snowing or drizzling or thunderstorm
        if any_percip:
            logger.bind(odd=True).trace(json.dumps(w))
        precipitation = {
            'raining': raining,
            'snowing': snowing,
            'drizzling': drizzling,
            'thunderstorm': thunderstorm,
            'any': any_percip
        }

        temp = w['main']['temp']
        humidity = w['main']['humidity']

        pressure = w['main']['pressure']

        wind = w.get('wind', {})
        # this is the rain/snow volume for the last 1h and 3h
        rain = w.get('rain', {})
        snow = w.get('snow', {})

        dt = w['dt']
        # misnomer on my behalf
        # .fromtimestamp() -> converts to our tz (from UTC)
        # .utcfromtimestamp() -> returns in UTC
        weather_dt = datetime.fromtimestamp(dt).isoformat()

        return {
            'temp': temp,
            'desc': desc,
            'humidity': humidity,
            'wind': wind,
            'rain': rain,
            'main': main,
            'snow': snow,
            'pressure': pressure,
            'precipitation': precipitation
        }

    def loop(self):
        while True:
            nowcast = self.get_nowcast()
            self.send(nowcast)
            time.sleep(self.frequency)

def pub(addr):
    freq = 60 * 5 # 5 mins

    publisher = NowcastPublisher(addr, "fhain", freq, lat_lon, msl, {})
    publisher.loop()
    #time.sleep(5.0) # bah
    #logger.debug("done sleeping")

    # while True:
    #     nowcast = publisher.get_nowcast()
    #     publisher.send(nowcast)

    #     #publisher.send_weather(weather)

    #     time.sleep(freq)


@catch()
def main():
    config = init("weather_pub", fullconfig=True)
    addr = config['temper_pub']['addr']

    pub(addr)
