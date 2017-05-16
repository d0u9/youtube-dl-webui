#!/usr/bin/env python
# -*- coding: utf-8 -*-

import youtube_dl

from multiprocessing import Process
from copy import deepcopy

WQ_DICT = {'from': 'worker'}

class Worker(Process):
    def __init__(self, tid, wqueue, param=None, ydl_opts=None):
        super(Worker, self).__init__()
        self.tid = tid
        self.wq = wqueue
        self.param = param
        self.ydl_opts = ydl_opts


    def run(self):
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            info_dict = ydl.extract_info(self.param['url'], download=False)
            wqd = deepcopy(WQ_DICT)
            wqd['tid'] = self.tid
            wqd['msgtype'] = 'info_dict'
            wqd['data'] = info_dict
            self.wq.put(wqd)


