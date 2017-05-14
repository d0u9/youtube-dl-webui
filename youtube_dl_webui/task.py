#!/usr/bin/env python
# -*- coding: utf-8 -*-

import multiprocessing
import copy

from multiprocessing.managers import BaseManager
from collections import deque
from hashlib import sha1
from time import time

from .downloader import downloader


class task_desc():
    state_index = {'downloading': 1, 'paused': 2, 'finished': 3}
    def __init__(self, url, opts, params={}):
        self.tid = sha1(url.encode()).hexdigest()
        self.info = {
                        'tid': self.tid,
                     'title': '',
                       'url': url,
                  'filename': '',
               'create_time': time(),
               'finish_time': time(),
                    'format': 0
                }

        self.status = {
                        'tid': self.tid,
                      'state': task_desc.state_index['paused'],
                    'percent': '0.0%',
                   'filename': '',
                'tmpfilename': '',
           'downloaded_bytes': 0,
                'total_bytes': 0,
       'total_bytes_estimate': 0,
                      'speed': 0,
                        'eta': 0,
                    'elapsed': 0,
                 'start_time': time(),
                 'pause_time': time(),
                       'log' : deque(maxlen=opts['log_size'])
                }


    def get_exerpt(self):
        exerpt_keys = set(['tid', 'url', 'title', 'percent'])
        exerpt = {}

        for key, val in self.info.items():
            if key in exerpt_keys:
                exerpt[key] = val

        for key, val in self.status.items():
            if key in exerpt_keys:
                exerpt[key] = val

        return exerpt


    def update_from_info_dict(self, info_dict):
        self.info['title'] = info_dict['title']
        self.info['format'] = info_dict['format']


    def get_status(self):
        data = copy.deepcopy(self.status)

        log = []
        for l in self.status.get('log'):
            log.append(l)

        data['log'] = log
        return data


    def get_info(self):
        data = copy.deepcopy(self.info)
        return data


    def set_item(self, item, val, override=False):
        self.set_info_item(item, val, override)
        self.set_status_item(item, val, override)


    def set_info_item(self, item, val, override=False):
        if override is True or self.info.get(item, None) is not None:
            self.info[item] = val


    def set_status_item(self, item, val, override=False):
        if override is True or self.status.get(item, None) is not None:
            self.status[item] = val


    def get_item(self, item):
        a = self.get_info_item(item)

        if a is None:
            return self.get_status_item(item)
        else:
            return a


    def get_info_item(self, item):
        return self.info.get(item, None)


    def get_status_item(self, item):
        return self.status.get(item,None)


    def set_state(self, state):
        if state not in task_desc.state_index:
            return False

        return self.set_status_item('state', task_desc.state_index[state])


    def push_log(self, log_type, log):
        valid_types = ['error', 'warning', 'debug']
        if log_type not in valid_types:
            return None

        self.status['log'].append({'type':log_type, 'time': int(time()), 'log': log})


class ydl_task():
    def __init__(self, param, desc, ydl_opts={}):
        self.tid = param['tid']
        self.param = param
        self.desc = desc
        self.ydl_opts = copy.deepcopy(ydl_opts.dict())
        self.downloader = None


    def delegate(self):
        self.downloader = downloader(self.param, self.desc, self.ydl_opts)


    def start_dl(self):
        self.desc.set_state('downloading')
        self.delegate()
        self.desc.set_status_item('start_time', time())
        self.downloader.start()


    def pause_dl(self):
        self.desc.set_state('paused')
        self.downloader.stop()

        cur_time = time()
        start_time = self.desc.get_item('start_time')
        elapsed = self.desc.get_item('elapsed')

        elapsed += cur_time - start_time
        self.desc.set_item('pause_time', cur_time)
        self.desc.set_item('elapsed', elapsed)


    def resume_dl(self):
        self.desc.set_state('downloading')
        self.delegate()
        self.desc.set_item('start_time', time())
        self.downloader.start()
