#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import logging

from multiprocessing import Process, Queue
from collections import deque
from sys import exit
from time import time
from os.path import expanduser

from .utils import state_name
from .db import DataBase
from .utils import TaskInexistenceError
from .utils import TaskRunningError
from .utils import TaskExistenceError
from .utils import TaskPausedError
from .server import Server
from .worker import Worker


class Core(object):
    exerpt_keys = ['tid', 'state', 'percent', 'total_bytes', 'title', 'eta', 'speed']
    valid_opts = ['proxy', 'format']

    def __init__(self, args=None):
        self.logger = logging.getLogger('ydl_webui')

        # options from command line
        self.cmdl_args_dict = {}
        # options read from configuration file
        self.conf_file_dict = {}
        # configuration options combined cmdl_args_dict with conf_file_dict.
        self.conf = {'server': {}, 'ydl': {}}

        self.rq = Queue()
        self.wq = Queue()
        self.worker = {}

        self.load_cmdl_args(args)
        self.load_conf_file()
        self.cmdl_override_conf_file()

        self.server = Server(self.wq, self.rq, self.conf['server']['host'], self.conf['server']['port'])
        self.db = DataBase(self.conf['db_path'])

        dl_dir = self.conf['download_dir']
        try:
            os.makedirs(dl_dir, exist_ok=True)
            self.logger.info("Download dir: %s", dl_dir)
            os.chdir(dl_dir)
        except PermissionError:
            self.logger.critical('Permission Error for download dir: %s', dl_dir)
            exit(1)

        self.launch_unfinished()
        self.server.start()


    def run(self):
        while True:
            data = self.rq.get()
            data_from = data.get('from', None)
            if data_from == 'server':
                ret = self.server_request(data)
                self.wq.put(ret)
            elif data_from == 'worker':
                ret = self.worker_request(data)
            else:
                logger.debug(data)


    def launch_unfinished(self):
        tlist = self.db.get_unfinished()
        for t in tlist:
            self.start_task(t, ignore_state=True)


    def create_task(self, param, ydl_opts):
        if 'url' not in param:
            raise KeyError

        if param['url'].strip() == '':
            raise KeyError

        tid = self.db.create_task(param, ydl_opts)
        return tid


    def start_task(self, tid, ignore_state=False, first_run=False):
        try:
            param = self.db.get_param(tid)
            ydl_opts = self.db.get_opts(tid)
        except TaskInexistenceError as e:
            raise TaskInexistenceError(e.msg)

        log_list = self.db.start_task(tid, ignore_state)
        self.launch_worker(tid, log_list, param=param, ydl_opts=ydl_opts, first_run=first_run)


    def pause_task(self, tid):
        self.cancel_worker(tid)


    def delete_task(self, tid):
        try:
            self.cancel_worker(tid)
        except TaskInexistenceError as e:
            raise e
        except:
            pass

        self.db.delete_task(tid)


    def launch_worker(self, tid, log_list, param=None, ydl_opts={}, first_run=False):
        if tid in self.worker:
            raise TaskRunningError('task already running')

        self.worker[tid] ={'obj': None, 'log': deque(maxlen=10)}

        for l in log_list:
            self.worker[tid]['log'].appendleft(l)

        self.worker[tid]['log'].appendleft({'time': int(time()), 'type': 'debug', 'msg': 'Task starts...'})
        self.db.update_log(tid, self.worker[tid]['log'])

        opts = self.add_ydl_conf_file_opts(ydl_opts)

        # launch worker process
        w = Worker(tid, self.rq, param=param, ydl_opts=opts, first_run=first_run)
        w.start()
        self.worker[tid]['obj'] = w


    def add_ydl_conf_file_opts(self, ydl_opts={}):
        conf_opts = self.conf.get('ydl', {})

        # filter out unvalid options
        d = {k: ydl_opts[k] for k in ydl_opts if k in Core.valid_opts}

        return {**conf_opts, **d}


    def cancel_worker(self, tid):
        if tid not in self.worker:
            raise TaskPausedError('task not running')

        w = self.worker[tid]
        self.db.cancel_task(tid, log=w['log'])
        w['obj'].stop()
        self.worker[tid]['log'].appendleft({'time': int(time()), 'type': 'debug', 'msg': 'Task stops...'})
        self.db.update_log(tid, self.worker[tid]['log'])

        del self.worker[tid]


    def load_cmdl_args(self, args):
        self.cmdl_args_dict['conf'] = args.get('config')
        self.cmdl_args_dict['host'] = args.get('host')
        self.cmdl_args_dict['port'] = args.get('port')


    def load_conf_file(self):
        try:
            with open(self.cmdl_args_dict['conf']) as f:
                self.conf_file_dict = json.load(f)
        except FileNotFoundError as e:
            self.logger.critical("Config file (%s) doesn't exist", self.cmdl_args_dict['conf'])
            exit(1)

        self.load_general_conf(self.conf_file_dict)
        self.load_server_conf(self.conf_file_dict)
        self.load_ydl_conf(self.conf_file_dict)


    def load_general_conf(self, conf_file_dict):
        # field1: key, field2: default value, field3: function to process the value
        valid_conf = [  ['download_dir',  '~/Downloads/youtube-dl',         expanduser],
                        ['db_path',       '~/.conf/youtube-dl-webui/db.db', expanduser],
                        ['task_log_size', 10,                                None],
                     ]

        general_conf = conf_file_dict.get('general', {})

        for conf in valid_conf:
            if conf[2] is None:
                self.conf[conf[0]] = general_conf.get(conf[0], conf[1])
            else:
                self.conf[conf[0]] = conf[2](general_conf.get(conf[0], conf[1]))


    def load_server_conf(self, conf_file_dict):
        valid_conf = [  ['host', '127.0.0.1'],
                        ['port', '5000'     ]
                     ]

        server_conf = conf_file_dict.get('server', {})

        for pair in valid_conf:
            self.conf['server'][pair[0]] = server_conf.get(pair[0], pair[1])


    def load_ydl_conf(self, conf_file_dict):
        ydl_opts = conf_file_dict.get('youtube_dl', {})

        for opt in Core.valid_opts:
            if opt in ydl_opts:
                self.conf['ydl'][opt] = ydl_opts.get(opt, None)


    def cmdl_override_conf_file(self):
        if self.cmdl_args_dict['host'] is not None:
            self.conf['server']['host'] = self.cmdl_args_dict['host']

        if self.cmdl_args_dict['port'] is not None:
            self.conf['server']['port'] = self.cmdl_args_dict['port']


    def server_request(self, data):
        msg_internal_error = {'status': 'error', 'errmsg': 'Internal Error'}
        msg_task_existence_error = {'status': 'error', 'errmsg': 'URL is already added'}
        msg_task_inexistence_error = {'status': 'error', 'errmsg': 'Task does not exist'}
        msg_url_error = {'status': 'error', 'errmsg': 'URL is invalid'}
        if data['command'] == 'create':
            try:
                tid = self.create_task(data['param'], {})
                self.start_task(tid, first_run=True)
            except TaskExistenceError:
                return msg_task_existence_error
            except TaskInexistenceError:
                return msg_internal_error
            except KeyError:
                return msg_url_error

            return {'status': 'success', 'tid': tid}

        if data['command'] == 'delete':
            try:
                self.delete_task(data['tid'])
            except TaskInexistenceError:
                return msg_task_inexistence_error

            return {'status': 'success'}

        if data['command'] == 'manipulate':
            tid = data['tid']
            try:
                if data['act'] == 'pause':
                    self.pause_task(tid)
                elif data['act'] == 'resume':
                    self.start_task(tid)
            except TaskPausedError:
                return {'status': 'error', 'errmsg': 'task paused already'}
            except TaskRunningError:
                return {'status': 'error', 'errmsg': 'task running already'}
            except TaskInexistenceError:
                return msg_task_inexistence_error

            return {'status': 'success'}

        if data['command'] == 'query':
            tid = data['tid']
            try:
                ret = self.db.query_task(tid)
            except TaskInexistenceError:
                return msg_task_inexistence_error

            detail = {}
            if data['exerpt'] is True:
                detail = {k: ret[k] for k in ret if k in Core.exerpt_keys}
            else:
                detail = ret

            return {'status': 'success', 'detail': detail}

        if data['command'] == 'list':
            state = data['state']
            if state not in state_name:
                return {'status': 'error', 'errmsg': 'invalid query state'}

            ret, counter = self.db.list_task(state)

            detail = []
            if data['exerpt'] is True:
                for each in ret:
                    d = {k: each[k] for k in each if k in Core.exerpt_keys}
                    detail.append(d)
            else:
                detail = ret

            return {'status': 'success', 'detail': detail, 'state_counter': counter}

        if data['command'] == 'state':
            return self.db.list_state()


    def worker_request(self, data):
        tid = data['tid']
        msgtype = data['msgtype']

        if msgtype == 'info_dict':
            self.db.update_from_info_dict(tid, data['data'])
            return

        if msgtype == 'log':
            if tid not in self.worker:
                return

            self.worker[tid]['log'].appendleft(data['data'])
            self.db.update_log(tid, self.worker[tid]['log'])

        if msgtype == 'progress':
            d = data['data']

            if d['status'] == 'downloading':
                self.db.progress_update(tid, d)

            if d['status'] == 'finished':
                self.worker[tid]['log'].appendleft({'time': int(time()), 'type': 'debug', 'msg': 'Task is done'})
                self.cancel_worker(tid)
                self.db.progress_update(tid, d)
                self.db.set_state(tid, 'finished')

        if msgtype == 'fatal':
            d = data['data']

            if d['type'] == 'invalid_url':
                self.logger.error("Can't start downloading {}, url is invalid".format(d['url']))
                self.db.set_state(tid, 'invalid')

