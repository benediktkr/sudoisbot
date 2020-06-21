#!/usr/bin/env python3

# https://ubntwiki.com/products/software/unifi-controller/api
# https://github.com/calmh/unifi-api/blob/master/unifi/controller.py

import json
from urllib.parse import urljoin

import urllib3
urllib3.disable_warnings()
import requests
from loguru import logger

from sudoisbot.common import init

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
        logger.debug(f"logging in to '{self._base_url}' as '{user}'")

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

    def get_client_names(self):
        # move this outside of the class
        names = list()
        for client in self.get_connected_clients():
            try:
                name = client.get('hostname', client['ip'])
                logger.trace(f"{client['essid']}: {name}")
                names.append(name)
            except KeyError:
                # device has niehter ip nor hostname, some fuckery
                # is going on
                logger.warnings(f"weird client on unifi: {client}")
        return names

def show_clients():
    config = init(__name__)
    api = UnifiApi(config)
    for client in api.get_clients_short():
        logger.info(client)

if __name__ == "__main__":
    show_clients()
