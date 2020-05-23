#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

from loguru import logger

from sudoisbot import listener, common



if __name__ == '__main__':
    main()

def main():
    parser = argparse.ArgumentParser("Telegram bot @sudoisbot listener")
    parser.add_argument("-d", "--daemon", action="store_true", help="Run as daemon")
    args = parser.parse_args()

    listener.main()
