#!/usr/bin/env python
# -*- coding: utf-8 -*-

import multiprocessing
from downloader import downloader
from hashlib import sha1

class task_status():
    def __init__(self, url):
        self.lock = multiprocessing.Lock()
        self._data = {
                        'id': sha1(url.encode()).hexdigest(),
                     'title': '',
                       'url': url,
                  'progress': '0.0'
                }

    def get_exerpt(self):
        exerpt_keys = set(['id', 'url', 'title', 'progress'])
        exerpt = {}

        with self.lock:
            for key, val in self._data.items():
                if key in exerpt_keys:
                    exerpt[key] = val

        return exerpt

    def update_from_info_dict(self, info_dict):
        with self.lock:
            self._data['title'] = info_dict['title']

        print ('xxxxx')
        print (self._data)


class ydl_task():
    def __init__(self, task_info, ydl_conf={}):
        self.ydl_conf = ydl_conf

        self.task_info = task_info
        self.task_status = task_status(task_info['url'])

        self.downloader = downloader(self.task_info, self.task_status, ydl_conf)

    def start_dl(self):
        self.downloader.start()

    def stop_dl(self):
        self.downloader.stop()

    def pause_dl(self):
        self.downloader.stop()

    def resume_dl(self):
        pass

    def del_task(self):
        self.stop_dl()
