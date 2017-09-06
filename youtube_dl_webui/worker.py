#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import logging
import json

from youtube_dl import YoutubeDL
from youtube_dl import DownloadError

from multiprocessing import Process
from time import time
from copy import deepcopy

WQ_DICT = {'from': 'worker'}
MSG = None


class YdlHook(object):
    def __init__(self, tid, msg_cli):
        self.logger = logging.getLogger('ydl_webui')
        self.tid = tid
        self.msg_cli = msg_cli
        #  self.wqd = deepcopy(WQ_DICT)
        #  self.wqd['tid'] = self.tid
        #  self.wqd['msgtype'] = 'progress'
        #  self.wqd['data'] = None


    def finished(self, d):
        self.logger.debug('finished status')
        #  d['_percent_str'] = '100%'
        #  d['speed'] = '0'
        #  d['elapsed'] = 0
        #  d['eta'] = 0
        #  d['downloaded_bytes'] = d['total_bytes']

        #  return d


    def downloading(self, d):
        self.logger.debug('downloading status')
        #  return d


    def error(self, d):
        self.logger.debug('error status')
        #  d['_percent_str'] = '100%'
        #  return d


    def dispatcher(self, d):
        pass
        #  if 'total_bytes_estimate' not in d:
            #  d['total_bytes_estimate'] = 0
        #  if 'tmpfilename' not in d:
            #  d['tmpfilename'] = ''

        #  if d['status'] == 'finished':
            #  d = self.finished(d)
        #  elif d['status'] == 'downloading':
            #  d = self.downloading(d)
        #  elif d['error'] == 'error':
            #  d = self.error(d)

        #  self.wqd['data'] = d
        #  self.wq.put(self.wqd)


class LogFilter(object):
    def __init__(self, tid, msg_cli):
        self.logger = logging.getLogger('ydl_webui')
        self.tid = tid
        self.msg_cli = msg_cli

    def debug(self, msg):
        self.logger.debug('debug: %s' %(self.ansi_escape(msg)))
        payload = {'time': int(time()), 'type': 'debug', 'msg': self.ansi_escape(msg)}
        self.msg_cli.put('log', {'tid': self.tid, 'data': payload})

    def warning(self, msg):
        self.logger.debug('warning: %s' %(self.ansi_escape(msg)))
        payload = {'time': int(time()), 'type': 'warning', 'msg': self.ansi_escape(msg)}
        self.msg_cli.put('log', {'tid': self.tid, 'data': payload})

    def error(self, msg):
        self.logger.debug('error: %s' %(self.ansi_escape(msg)))
        payload = {'time': int(time()), 'type': 'warning', 'error': self.ansi_escape(msg)}
        self.msg_cli.put('log', {'tid': self.tid, 'data': payload})

    def ansi_escape(self, msg):
        reg = r'\x1b\[([0-9,A-Z]{1,2}(;[0-9]{1,2})?(;[0-9]{3})?)?[m|K]?'
        return re.sub(reg, '', msg)


class fatal_event(object):
    def __init__(self, tid, wqueue):
        pass
        #  self.tid = tid
        #  self.wq = wqueue
        #  self.wqd = deepcopy(WQ_DICT)
        #  self.wqd['tid'] = self.tid
        #  self.wqd['msgtype'] = 'fatal'
        #  self.data = {'time': None, 'type': None, 'msg': None}
        #  self.wqd['data'] = self.data


    def invalid_url(self, url):
        pass
        #  self.data['time'] = int(time())
        #  self.data['type'] = 'invalid_url'
        #  self.data['url'] = url;
        #  self.data['msg'] = 'invalid url: {}'.format(url)
        #  self.wq.put(self.wqd)


class Worker(Process):
    def __init__(self, tid, url, msg_cli, ydl_opts=None, first_run=False):
        super(Worker, self).__init__()
        self.logger = logging.getLogger('ydl_webui')
        self.tid = tid
        self.url = url
        self.msg_cli = msg_cli
        self.ydl_opts = ydl_opts
        self.first_run = first_run
        self.log_filter = LogFilter(tid, msg_cli)
        self.ydl_hook = YdlHook(tid, msg_cli)

    def intercept_ydl_opts(self):
        self.ydl_opts['logger'] = self.log_filter
        self.ydl_opts['progress_hooks'] = [self.ydl_hook.dispatcher]
        self.ydl_opts['noplaylist'] = "false"

    def run(self):
        self.intercept_ydl_opts()
        with YoutubeDL(self.ydl_opts) as ydl:
            try:
                if self.first_run:
                    print(self.url)
                    info_dict = ydl.extract_info(self.url, download=False)

                    #  self.logger.debug(json.dumps(info_dict, indent=4))
                    print(info_dict['like_count'])

                    info_dict['description'] = info_dict['description'].replace('\n', '<br />');
                    payload = {'tid': self.tid, 'data': info_dict}
                    self.msg_cli.put('info_dict', payload)

                self.logger.info('start downloading ...')
                #  ydl.download([self.url])
            except DownloadError as e:
                # url error
                #  event_handle = fatal_event(self.tid, self.wq)
                #  event_handle.invalid_url(self.url);
                pass


    def stop(self):
        self.logger.info('Terminating Process ...')
        self.terminate()
        self.join()

