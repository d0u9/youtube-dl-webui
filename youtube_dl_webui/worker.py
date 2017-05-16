#!/usr/bin/env python
# -*- coding: utf-8 -*-

import youtube_dl

from multiprocessing import Process
from copy import deepcopy

WQ_DICT = {'from': 'worker'}

class Worker(Process):
    def __init__(self, tid, wqueue, param=None, ydl_opts=None, first_run=False):
        super(Worker, self).__init__()
        self.tid = tid
        self.wq = wqueue
        self.param = param
        self.url = param['url']
        self.ydl_opts = ydl_opts
        self.first_run = first_run


    def run(self):
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

