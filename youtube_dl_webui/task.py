#!/usr/bin/env python
# -*- coding: utf-8 -*-

import multiprocessing
import copy

from downloader import downloader
from hashlib import sha1

class task_status():
    def __init__(self, url):
        self.states = {'downloading': 1, 'paused': 2, 'finished': 3}
        self._data = {
                        'id': sha1(url.encode()).hexdigest(),
                     'title': '',
                       'url': url,
                  'progress': '0.0',
                     'state': self.states['paused']
                }

    def get_exerpt(self):
        exerpt_keys = set(['id', 'url', 'title', 'progress'])
        exerpt = {}

        for key, val in self._data.items():
            if key in exerpt_keys:
                exerpt[key] = val

        return exerpt

    def update_from_info_dict(self, info_dict):
        self._data['title'] = info_dict['title']


    def get_status(self):
        return self._data

    def set_state(self, state):
        if state not in self.states:
            return False

        self._data['state'] = self.states[state]

        return True


class ydl_task():
    def __init__(self, info, status, ydl_opts={}):
        self.tid = info['tid']
        self.info =info
        self.status = status
        self.ydl_opts = copy.deepcopy(ydl_opts.dict())
        self.downloader = None

    def delegate(self):
        self.downloader = downloader(self.info, self.status, self.ydl_opts)


    def start_dl(self):
        self.status.set_state('downloading')
        self.delegate()
        self.downloader.start()


    def pause_dl(self):
        self.status.set_state('paused')
        self.downloader.stop()


    def resume_dl(self):
        self.status.set_state('downloading')
        self.delegate()
        self.downloader.start()

    def del_task(self):
        pass
        #  self.stop_dl()
