#!/usr/bin/env python3

# https://ubntwiki.com/products/software/unifi-controller/api
# https://github.com/calmh/unifi-api/blob/master/unifi/controller.py

import json
from urllib.parse import urljoin
from itertools import groupby
from datetime import datetime, timezone

import urllib3
urllib3.disable_warnings()
import requests
from requests.exceptions import RequestException, ConnectionError
from loguru import logger

from sudoisbot.common import init
from sudoisbot.network.pub import Publisher

class UnifiPublisher(Publisher):
    def __init__(self, addr, freq, unifi_config, people, location):
        super().__init__(addr, b"unifi", "unifi", freq)

        self.unifi_config = unifi_config
        self.people = people
        self.location = location

    def publish(self):

        try:
            # constructor logs in
            api = UnifiApi(self.unifi_config)
            wifi_clients = api.get_client_names()
        except ConnectionError as e:
            logger.warning(e)
            return
        except RequestException as e:
            logger.error(e)
            raise # ???

        home = dict()
        for initials, devices in self.people.items():
            data = {
                'measurement': 'people',
                'time':  datetime.now(timezone.utc).isoformat(),
                'tags': {
                    'name': initials,
                    'frequency': self.frequency,
                    'location': self.location
                },
                'fields': {
                    'home': any(d in wifi_clients for d in devices)
                }
            }

            print(data)
            self.pub(data)

class UnifiApi(object):
    def __init__(self, unifi_config):
        # unifi config comes from the yaml config files (might change),
        # caller is responsible for loading that (or constructing
        # in some other way), as well as setting loguru sinks
        #
        # makes a login request
        #
        # unhandled KeyError for missig variables
        self._base_url = unifi_config['url']
        self._session = requests.Session()

        user = unifi_config['username']
        logger.trace(f"logging in to '{self._base_url}' as '{user}'")

        login = self.request(
            "post",
            "/api/login",
            verify=unifi_config.get("ssl_verify", False),
            json = { "username": unifi_config['username'],
                     "password": unifi_config['password']})

    def request(self, method, endpoint, **kwargs):
        url = urljoin(self._base_url, endpoint)
        try:
            response = self._session.request(method.upper(), url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.HTTPError):
                # dont log stacktrace at all for http errors
                logger.error(e)
            else:
                logger.exception(e)
            raise

    def get_connected_clients(self):
        clients = self.request("get", "/api/s/default/stat/sta")
        return clients.json()['data']

    def get_clients_short(self):
        clients = list()
        for client in self.get_connected_clients():
            clients.append({'hostname': client.get('hostname', None),
                           'ip': client['ip'],
                           'essid': client['essid']})
        return clients

    def get_clients_by_ssid(self):
        clients = sorted(self.get_clients_short(), key=lambda x: x['essid'])
        by_ssid = groupby(clients, lambda c: c['essid'])
        return {k: list(g) for (k, g) in by_ssid}

    def get_client_names(self):
        names = list()
        for client in self.get_connected_clients():
            try:
                name = client.get('hostname', client['ip'])
                logger.trace(f"{client['essid']}: {name}")
                names.append(name)
            except KeyError:
                # device is mimissing ip, hostname or ssid, some fuckery
                # is going on
                logger.warning(f"weird client on unifi: {client}")
        return names

def main(config):

    addr = config['addr']
    name = 'unifi'
    sleep = 60
    unifi_config = config['unifi']
    people = config['people']
    location = config['location']

    with UnifiPublisher(addr, sleep, unifi_config, people, location) as pub:
        pub.loop()


def show_clients(config):
    unifi_config = config['unifi']

    api = UnifiApi(unifi_config)
    for client in api.get_clients_short():
        logger.info(client)
