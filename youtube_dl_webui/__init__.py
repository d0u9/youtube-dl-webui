#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from argparse import ArgumentParser

from .config import config
from .server import server
from .manager import ydl_manger


def getopt(argv):
    parser = ArgumentParser(description='Another webui for youtube-dl')

    parser.add_argument('-c', '--config', metavar="CONFIG_FILE", required=True, help="config file")
    parser.add_argument('--host', metavar="ADDR", help="the address server listens on")
    parser.add_argument('--port', metavar="PORT", help="the port server listens on")

    return parser.parse_args()


def main(argv=None):
    from os import getpid

    print("pid is {}".format(getpid()))

    #------------------------------------
    cmd_args = getopt(argv)
    conf = config(cmd_args)

    manager = ydl_manger(conf.manager)

    s = server(conf.server)
    s.bind_ydl_manager(manager)
    s.run()
    """


    tid1 = manager.create_task({'url': 'https://www.youtube.com/watch?v=daVDrGsaDME'})
    print ('create new task: id = {}'.format(tid1))
    tid2 = manager.create_task({'url': 'https://www.youtube.com/watch?v=daVDrGsaQQQ'})
    print ('create new task: id = {}'.format(tid2))

    from time import sleep
    sleep(1)

    print("-------------------------------------------------")
    sleep(1)

    manager.start_task(tid1)
    status = manager.get_task_desc(tid1)
    print ('current_task_status {}'.format(str(status)))

    sleep(1)
    manager.pause_task(tid1)
    status = manager.get_task_desc(tid1)
    print ('current_task_status {}'.format(str(status)))

    sleep(1)
    manager.resume_task(tid1)
    status = manager.get_task_desc(tid1)
    print ('current_task_status {}'.format(str(status)))

    print(manager.list_tasks(state='downloading'))
    print("-------------------------------------------------")
    print(manager.query_task(tid1))

    print("-------------------------------------------------")
    sleep(10)
    status = manager.get_task_desc(tid1)
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(status)

    sleep(1000)

    """


