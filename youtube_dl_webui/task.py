#!/usr/bin/env python
# -*- coding: utf-8 -*-

import multiprocessing
import copy

from multiprocessing.managers import BaseManager
from collections import deque
from hashlib import sha1
from time import time

from .downloader import downloader


class task_status():
    def __init__(self, url, opts, params={}):
        self.states = {'downloading': 1, 'paused': 2, 'finished': 3}
        self._data = {
                        'id': sha1(url.encode()).hexdigest(),
                     'title': '',
                       'url': url,
                   'percent': '0.0',
                  'filename': '',
               'tmpfilename': '',
          'downloaded_bytes': 0,
               'total_bytes': 0,
      'total_bytes_estimate': 0,
                     'speed': 0,
                       'eta': 0,
                   'elapsed': 0,
               'create_time': time(),
                'start_time': time(),
                'pause_time': time(),
               'finish_time': time(),
                    'format': 0,
                     'state': self.states['paused'],
                      'log' : deque(maxlen=opts.log_size)
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
        self._data['format'] = info_dict['format']


    def get_status(self):
        data = copy.deepcopy(self._data)
        log = []
        for l in self._data.get('log'):
            log.append(l)

        data['log'] = log
        return data


    def set_item(self, item, val):
        if item not in self._data:
            return None

        self._data[item] = val

        return True


    def get_item(self, item):
        if item not in self._data:
            return None

        return self._data[item]


    def set_state(self, state):
        if state not in self.states:
            return False

        return self.set_item('state', self.states[state])


    def push_log(self, log_type, log):
        valid_types = ['error', 'warning', 'debug']
        if log_type not in valid_types:
            return None

        self._data['log'].append({'type':log_type, 'time': int(time()), 'log': log})


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
        self.status.set_item('start_time', time())
        self.downloader.start()


    def pause_dl(self):
        self.status.set_state('paused')
        self.downloader.stop()

        cur_time = time()
        start_time = self.status.get_item('start_time')
        elapsed = self.status.get_item('elapsed')

        elapsed += cur_time - start_time
        self.status.set_item('pause_time', cur_time)
        self.status.set_item('elapsed', elapsed)


    def resume_dl(self):
        self.status.set_state('downloading')
        self.delegate()
        self.status.set_item('start_time', time())
        self.downloader.start()
