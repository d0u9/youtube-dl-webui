#!/usr/bin/env python
# -*- coding: utf-8 -*-

from multiprocessing import Process

class Worker(Process):
    def __init__(self, tid, wqueue, param=None, ydl_opts=None):
        super(Worker, self).__init__()
        self.tid = tid
        self.wq = wqueue
        self.param = param
        self.ydl_opts = ydl_opts

    def run(self):
        from time import sleep
        while True:
            sleep(1)
            print('hello')
            self.wq.put({'from': 'worker', 'tid': self.tid})
            print(self.param)
            print(self.ydl_opts)

