#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from argparse import ArgumentParser

from config import config
from server import server
from manager import ydl_manger


def getopt(argv):
    parser = ArgumentParser(description='Another webui for youtube-dl')

    parser.add_argument('-c', '--config', metavar="CONFIG_FILE", required=True, help="config file")
    parser.add_argument('--host', metavar="ADDR", help="the address server listens on")
    parser.add_argument('--port', metavar="PORT", help="the port server listens on")

    return parser.parse_args()


def main(argv=None):
    args = getopt(argv)
    conf = config(args)

    m = ydl_manger(conf.manager)

    tid1 = m.create_task({'url': 'https://www.youtube.com/watch?v=daVDrGsaDME'})
    print ('create new task: id = {}'.format(tid1))
    tid2 = m.create_task({'url': 'https://www.youtube.com/watch?v=daVDrGsaQQQ'})
    print ('create new task: id = {}'.format(tid2))

    from time import sleep
    sleep(1)
    status = m.get_task_status(tid1)
    #  print ('current_task_status {}'.format(str(status)))
    #  status = m.get_task_status(tid2)
    #  print ('current_task_status {}'.format(str(status)))

    print("-------------------------------------------------")
    sleep(10)

    #  s = server()
    #  s.run(conf.server)



