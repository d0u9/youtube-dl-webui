#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from argparse import ArgumentParser

from .core import Core

def getopt(argv):
    parser = ArgumentParser(description='Another webui for youtube-dl')

    parser.add_argument('-c', '--config', metavar="CONFIG_FILE", required=True, help="config file")
    parser.add_argument('--host', metavar="ADDR", help="the address server listens on")
    parser.add_argument('--port', metavar="PORT", help="the port server listens on")

    return vars(parser.parse_args())


def main(argv=None):
    from os import getpid

    print("pid is {}".format(getpid()))
    print("-----------------------------------")

    cmd_args = getopt(argv)
    core = Core(args=cmd_args)

    core.create_task({'url': '1322af23123x'}, {'proxy': 'localhsot'})

