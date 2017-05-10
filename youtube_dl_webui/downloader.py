#!/usr/bin/env python
# -*- coding: utf-8 -*-

import youtube_dl
import json
import copy

from multiprocessing import Process
from time import time

class log_filter(object):
    def __init__(self, status):
        self.status = status


    def debug(self, msg):
        self.status.push_log('debug', msg)


    def warning(self, msg):
        self.status.push_log('warning', msg)


    def error(self, msg):
        self.status.push_log('error', msg)


class downloader(Process):
    def __init__(self, info, status, ydl_opts):
        Process.__init__(self, group=None, target=None, name=None, args=(), kwargs={}, daemon=None)
        self.tid = info['tid']
        self.info = info
        self.status = status
        self.ydl_opts = ydl_opts

        self.log_filter = log_filter(status)


    def run(self):
        print ('start downloading... {}'.format(self.status.get_status()))

        # For tests below, delete after use
        info_dict = {'title': 'this is a test title', 'file': 'hello file'}
        self.status.update_from_info_dict(info_dict)

        from time import sleep
        from random import randint
        #  sleep(randint(5, 10))
        t = 100 - self.status.get_item('elapsed')
        while t > 0:
            msg = "--- Time remain {}".format(t)
            print (msg)
            self.status.push_log('debug', msg)
            t -= 1
            sleep(1)


        # For tests above, delete after use


        """
        self.ydl_opts['logger'] = self.log_filter
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            print("downloading {}".format(self.info['url']))
            info_dict = ydl.extract_info(self.info['url'], download=False)

            self.status.update_from_info_dict(info_dict)
            ydl.download([self.info['url']])
        """


        self.status.set_state('finished')
        print ('download finished {}'.format(self.status.get_status()))

        cur_time = time()
        start_time = self.status.get_item('start_time')
        elapsed = self.status.get_item('elapsed')
        elapsed += cur_time - start_time
        self.status.set_item('finishe_time', cur_time)
        self.status.set_item('elapsed', elapsed)


    def update_ydl_conf(self, key, val):
        self.ydl_conf[key] = val

    def stop(self):
        self.terminate()
        self.join()
