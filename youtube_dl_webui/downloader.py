#!/usr/bin/env python
# -*- coding: utf-8 -*-

import youtube_dl
import json
import copy

from multiprocessing import Process

class log_filter(object):
    def __init__(self):
        self.info_dict = {}
        self.only_json = True

    def get_info_dict(self):
        return self.info_dict

    def debug(self, msg):

        # find the info_dict in the outputs
        if msg[0] is '{':
            try:
                j = json.loads(msg)
            except ValueError:
                return False

            #  print (msg)
            self.info_dict = j
            return True

        elif not self.only_json:
            print (msg)


    def warning(self, msg):
        #  print(msg)
        pass

    def error(self, msg):
        #  print(msg)
        pass

class downloader(Process):
    def __init__(self, info, status, ydl_opts):
        Process.__init__(self, group=None, target=None, name=None, args=(), kwargs={}, daemon=None)
        self.tid = info['tid']
        self.info = info
        self.status = status
        self.ydl_opts = ydl_opts

        self.log_filter = log_filter()


    def run(self):
        self.ydl_opts['forcejson'] = '1'
        self.ydl_opts['logger'] = self.log_filter
        self.ydl_opts['skip_download'] = '1'

        # For tests below, delete after use
        info_dict = {'title': 'this is a test title'}
        self.status.update_from_info_dict(info_dict)

        print ('start downloading... {}'.format(self.status.get_status()))

        from time import sleep
        from random import randint
        #  sleep(randint(5, 10))
        sleep(1000)


        self.status.set_state('finished')
        print ('download finished {}'.format(self.status.get_status()))

        # For tests above, delete after use

        #  with youtube_dl.YoutubeDL(self.ydl_conf) as ydl:
            #  ydl.download([self.task_info.get('url')])

        #  self.task_status.update_from_info_dict(self.log_filter.get_info_dict())

        #  self.log_filter.only_json = False
        #  del self.ydl_conf['skip_download']
        #  with youtube_dl.YoutubeDL(self.ydl_conf) as ydl:
            #  ydl.download([self.task_info.get('url')])

    def update_ydl_conf(self, key, val):
        self.ydl_conf[key] = val

    def stop(self):
        self.terminate()
        self.join()
