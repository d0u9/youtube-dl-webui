#!/usr/bin/env python
# -*- coding: utf-8 -*-

import youtube_dl
import json

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
    def __init__(self, task_info, task_status, ydl_conf={}):
        Process.__init__(self, group=None, target=None, name=None, args=(), kwargs={}, daemon=None)
        self.task_info = task_info
        self.task_status = task_status
        self.ydl_conf = ydl_conf

        self.log_filter = log_filter()

    def run(self):
        self.ydl_conf['forcejson'] = '1'
        self.ydl_conf['logger'] = self.log_filter
        self.ydl_conf['skip_download'] = '1'
        with youtube_dl.YoutubeDL(self.ydl_conf) as ydl:
            ydl.download([self.task_info.get('url')])

        self.task_status.update_from_info_dict(self.log_filter.get_info_dict())

        self.log_filter.only_json = False
        del self.ydl_conf['skip_download']
        with youtube_dl.YoutubeDL(self.ydl_conf) as ydl:
            ydl.download([self.task_info.get('url')])

        print ("zzzz")

    def update_ydl_conf(self, key, val):
        self.ydl_conf[key] = val

    def stop(self):
        print ("stop")
        self.terminate()
