#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import copy
import pprint

from multiprocessing import Process
from time import time

import youtube_dl

G_desc = None

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
        global G_desc
        downloader.calc_stop_time(G_desc)
        print('Done downloading, now converting ...')


    @classmethod
    def downloading(cls, d):
        global G_desc
        G_desc.set_item('filename', d['filename'])
        G_desc.set_item('tmpfilename', d['tmpfilename'])
        G_desc.set_item('downloaded_bytes', d['downloaded_bytes'])
        if 'total_bytes' in d:
            G_desc.set_item('total_bytes', d['total_bytes'])
        else:
            G_desc.set_item('total_bytes_estimate', d['total_bytes_estimate'])
        G_desc.set_item('eta', d['eta'])
        G_desc.set_item('speed', d['speed'])
        G_desc.set_item('percent', d['_percent_str'])


    @classmethod
    def error(cls, d):
        print('error ...')


class log_filter(object):
    def __init__(self, desc):
        self.desc = desc


    def debug(self, msg):
        self.desc.push_log('debug', msg)


    def warning(self, msg):
        self.desc.push_log('warning', msg)


    def error(self, msg):
        self.desc.push_log('error', msg)


class downloader(Process):
    def __init__(self, param, desc, ydl_opts):
        Process.__init__(self, group=None, target=None, name=None, args=(), kwargs={}, daemon=None)
        self.tid = param['tid']
        self.param = param
        self.desc = desc
        self.ydl_opts = ydl_opts

        self.log_filter = log_filter(desc)

        global G_desc
        G_desc = desc


    def intercept_ydl_opts(self):
#        self.ydl_opts['logger'] = self.log_filter
        self.ydl_opts['progress_hooks'] = [ydl_hook.dispatcher]


    def run(self):
        print ('start downloading... {}'.format(self.desc.get_status()))
        pp = pprint.PrettyPrinter(indent=4)

        downloader.calc_start_time(self.desc)

        # For tests below, delete after use
        info_dict = {'title': 'this is a test title', 'format': 'test format'}
        self.desc.update_from_info_dict(info_dict)

        from time import sleep
        from random import randint
        #  sleep(randint(5, 10))
        t = 20 - self.desc.get_status_item('elapsed')
        while t > 0:
            msg = "--- Time remain {}".format(t)
            print (msg)
            self.desc.push_log('debug', msg)
            t -= 1
            sleep(1)

        downloader.calc_stop_time(self.desc)
        # For tests above, delete after use

        """

        self.intercept_ydl_opts()

        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            print("downloading {}".format(self.param['url']))
            info_dict = ydl.extract_info(self.param['url'], download=False)
            pp.pprint(info_dict)

            self.desc.update_from_info_dict(info_dict)
            ydl.download([self.param['url']])
        """


        self.desc.set_state('finished')
        print ('download finished {}'.format(self.desc.get_status()))


    @staticmethod
    def calc_start_time(desc):
        cur_time = time()
        desc.set_status_item('start_time', cur_time)


    @staticmethod
    def calc_stop_time(desc):
        cur_time = time()
        start_time = desc.get_status_item('start_time')
        elapsed = desc.get_status_item('elapsed')
        elapsed += cur_time - start_time
        desc.set_status_item('elapsed', elapsed)
        desc.set_status_item('pause_time', cur_time)


    def update_ydl_conf(self, key, val):
        self.ydl_conf[key] = val


    def stop(self):
        self.terminate()
        downloader.calc_stop_time(self.desc)
        self.join()
