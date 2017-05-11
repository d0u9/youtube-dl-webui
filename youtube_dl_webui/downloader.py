#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import copy
import pprint

from multiprocessing import Process
from time import time

import youtube_dl

status_global = None

class ydl_hook():
    @classmethod
    def dispatcher(cls, d):
        if d['status'] == 'downloading':
            cls.downloading(d)
        elif d['status'] == 'finished':
            cls.finished(d)
        elif d['status'] == 'error':
            cls.error(d)


    @classmethod
    def finished(cls, d):
        global status_global
        print('Done downloading, now converting ...')


    @classmethod
    def downloading(cls, d):
        global status_global
        status_global.set_item('filename', d['filename'])
        status_global.set_item('tmpfilename', d['tmpfilename'])
        status_global.set_item('downloaded_bytes', d['downloaded_bytes'])
        if 'total_bytes' in d:
            status_global.set_item('total_bytes', d['total_bytes'])
        else:
            status_global.set_item('total_bytes_estimate', d['total_bytes_estimate'])
        status_global.set_item('eta', d['eta'])
        status_global.set_item('speed', d['speed'])
        status_global.set_item('percent', d['_percent_str'])


    @classmethod
    def error(cls, d):
        print('error ...')


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

        global status_global
        status_global = status


    def intercept_ydl_opts(self):
#        self.ydl_opts['logger'] = self.log_filter
        self.ydl_opts['progress_hooks'] = [ydl_hook.dispatcher]
#        self.ydl_opts['progress_hooks'] = [hook]


    def run(self):
        print ('start downloading... {}'.format(self.status.get_status()))
        pp = pprint.PrettyPrinter(indent=4)

        # For tests below, delete after use
        """
        info_dict = {'title': 'this is a test title', 'file': 'hello file'}
        self.status.update_from_info_dict(info_dict)

        from time import sleep
        from random import randint
        #  sleep(randint(5, 10))
        t = 20 - self.status.get_item('elapsed')
        while t > 0:
            msg = "--- Time remain {}".format(t)
            print (msg)
            self.status.push_log('debug', msg)
            t -= 1
            sleep(1)

        # For tests above, delete after use


        """

        self.intercept_ydl_opts()

        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            print("downloading {}".format(self.info['url']))
            info_dict = ydl.extract_info(self.info['url'], download=False)
            pp.pprint(info_dict)

            self.status.update_from_info_dict(info_dict)
            ydl.download([self.info['url']])


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
