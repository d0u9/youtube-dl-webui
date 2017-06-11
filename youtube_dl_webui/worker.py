#!/usr/bin/env python
# -*- coding: utf-8 -*-

from youtube_dl import YoutubeDL
from youtube_dl import DownloadError

from multiprocessing import Process
from time import time
from copy import deepcopy

WQ_DICT = {'from': 'worker'}


class ydl_hook(object):
    def __init__(self, tid, wqueue):
        self.tid = tid
        self.wq = wqueue
        self.wqd = deepcopy(WQ_DICT)
        self.wqd['tid'] = self.tid
        self.wqd['msgtype'] = 'progress'
        self.wqd['data'] = None


    def finished(self, d):
        print('finished status')
        print(d)
        d['_percent_str'] = '100%'
        d['speed'] = '0'
        d['elapsed'] = 0
        d['eta'] = 0
        d['downloaded_bytes'] = d['total_bytes']

        return d


    def downloading(self, d):
        print('downloading status')
        print(d)
        d['_percent_str'] = '100%'
        return d


    def error(self, d):
        print('error status')
        print(d)
        d['_percent_str'] = '100%'
        return d


    def dispatcher(self, d):
        if 'total_bytes_estimate' not in d:
            d['total_bytes_estimate'] = 0
        if 'tmpfilename' not in d:
            d['tmpfilename'] = ''

        if d['status'] == 'finished':
            d = self.finished(d)
        elif d['status'] == 'downloading':
            d = self.downloading(d)
        elif d['error'] == 'error':
            d = self.error(d)

        self.wqd['data'] = d
        self.wq.put(self.wqd)


class log_filter(object):
    def __init__(self, tid, wqueue):
        self.tid = tid
        self.wq = wqueue
        self.wqd = deepcopy(WQ_DICT)
        self.wqd['tid'] = self.tid
        self.wqd['msgtype'] = 'log'
        self.data = {'time': None, 'type': None, 'msg': None}
        self.wqd['data'] = self.data


    def debug(self, msg):
        self.data['time'] = int(time())
        self.data['type'] = 'debug'
        self.data['msg'] = msg
        self.wq.put(self.wqd)


    def warning(self, msg):
        self.data['time'] = int(time())
        self.data['type'] = 'warning'
        self.data['msg'] = msg
        self.wq.put(self.wqd)


    def error(self, msg):
        self.data['time'] = int(time())
        self.data['type'] = 'error'
        self.data['msg'] = msg
        self.wq.put(self.wqd)


class fatal_event(object):
    def __init__(self, tid, wqueue):
        self.tid = tid
        self.wq = wqueue
        self.wqd = deepcopy(WQ_DICT)
        self.wqd['tid'] = self.tid
        self.wqd['msgtype'] = 'fatal'
        self.data = {'time': None, 'type': None, 'msg': None}
        self.wqd['data'] = self.data


    def invalid_url(self, url):
        self.data['time'] = int(time())
        self.data['type'] = 'invalid_url'
        self.data['url'] = url;
        self.data['msg'] = 'invalid url: {}'.format(url)
        self.wq.put(self.wqd)


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

        with YoutubeDL(self.ydl_opts) as ydl:
            try:
                if self.first_run:
                    info_dict = ydl.extract_info(self.url, download=False)
                    wqd = deepcopy(WQ_DICT)
                    wqd['tid'] = self.tid
                    wqd['msgtype'] = 'info_dict'
                    wqd['data'] = info_dict
                    self.wq.put(wqd)

                print('start downloading ...')
                ydl.download([self.url])
            except DownloadError as e:
                # url error
                event_handle = fatal_event(self.tid, self.wq)
                event_handle.invalid_url(self.url);


    def stop(self):
        print('Terminating Process ...')
        self.terminate()
        self.join()

