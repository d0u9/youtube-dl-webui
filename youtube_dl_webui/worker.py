#!/usr/bin/env python
# -*- coding: utf-8 -*-

import youtube_dl

from multiprocessing import Process
from copy import deepcopy

WQ_DICT = {'from': 'worker'}


class ydl_hook(object):
    def __init__(self, tid, wqueue):
        self.tid = tid
        self.wq = wqueue


    def dispatcher(self, d):
        v = {'HOOK': d}
        self.wq.put(v)


class log_filter(object):
    def __init__(self, tid, wqueue):
        self.tid = tid
        self.wq = wqueue


    def debug(self, msg):
        d = {'DEBUG': msg}
        self.wq.put(d)


    def warning(self, msg):
        d = {'WARN': msg}
        self.wq.put(d)


    def error(self, msg):
        d = {'ERROR': msg}
        self.wq.put(d)


class Worker(Process):
    def __init__(self, tid, wqueue, param=None, ydl_opts=None, first_run=False):
        super(Worker, self).__init__()
        self.tid = tid
        self.wq = wqueue
        self.param = param
        self.url = param['url']
        self.ydl_opts = ydl_opts
        self.first_run = first_run
        self.log_filter = log_filter(tid, self.wq)
        self.ydl_hook = ydl_hook(tid, self.wq)


    def intercept_ydl_opts(self):
        self.ydl_opts['logger'] = self.log_filter
        self.ydl_opts['progress_hooks'] = [self.ydl_hook.dispatcher]


    def run(self):
        self.intercept_ydl_opts()

        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            if self.first_run:
                info_dict = ydl.extract_info(self.url, download=False)
                wqd = deepcopy(WQ_DICT)
                wqd['tid'] = self.tid
                wqd['msgtype'] = 'info_dict'
                wqd['data'] = info_dict
                self.wq.put(wqd)

            print('start downloading ...')
            ydl.download([self.url])


    def stop(self):
        self.terminate()
        self.join()

