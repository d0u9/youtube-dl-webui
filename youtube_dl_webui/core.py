#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os

from multiprocessing import Process, Queue
from collections import deque

from .utils import state_name
from .db import DataBase
from .utils import TaskInexistenceError
from .utils import TaskRunningError
from .utils import TaskExistenceError
from .utils import TaskPausedError
from .server import Server
from .worker import Worker

class Core(object):
    exerpt_keys = ['tid', 'state', 'percent', 'total_bytes', 'title']
    valid_opts = ['proxy']

    def __init__(self, args=None):
        self.cmd_args = {}
        self.conf = {'server': {}, 'ydl': {}}
        self.rq = Queue()
        self.wq = Queue()
        self.server = Server(self.wq, self.rq)
        self.worker = {}

        if args is not None:
            self.load_cmd_args(args)

        self.load_conf_file()

        self.db = DataBase(self.conf['db_path'])

        self.launch_unfinished()
        self.server.start()


    def worker_request(self, data):
        print(data)


    def run(self):
        while True:
            data = self.rq.get()
            if data['from'] == 'server':
                ret = self.server_request(data)
            else:
                ret = self.worker_request(data)

            self.wq.put(ret)

    def launch_unfinished(self):
        tlist = self.db.get_unfinished()
        for t in tlist:
            self.start_task(t, ignore_state=True)


    def create_task(self, param, ydl_opts):
        if 'url' not in param:
            raise KeyError

        tid = self.db.create_task(param, ydl_opts)
        return tid


    def start_task(self, tid, ignore_state=False):
        try:
            param = self.db.get_param(tid)
            ydl_opts = self.db.get_opts(tid)
        except TaskInexistenceError as e:
            raise TaskInexistenceError(e.msg)

        log_list = self.db.start_task(tid, ignore_state)
        self.launch_worker(tid, log_list, param=param, ydl_opts=ydl_opts)


    def pause_task(self, tid):
        try:
            self.cancel_worker(tid)
        except:
            pass
        self.db.pause_task(tid)


    def delete_task(self, tid):
        try:
            self.cancel_worker(tid)
        except:
            pass
        self.db.delete_task(tid)


    def launch_worker(self, tid, log_list, param=None, ydl_opts={}):
        if tid in self.worker:
            raise TaskRunningError('task already running')

        self.worker[tid] ={'obj': None, 'log': deque(maxlen=10)}

        for l in log_list:
            self.worker[tid]['log'].append(l)

        opts = self.add_ydl_conf_file_opts(ydl_opts)

        # launch worker process
        w = Worker(tid, self.rq, param=param, ydl_opts=opts)
        w.start()
        self.worker[tid]['obj'] = w


    def add_ydl_conf_file_opts(self, ydl_opts={}):
        conf_opts = self.conf.get('ydl', {})

        # filter out unvalid options
        d = {k: ydl_opts[k] for k in ydl_opts if k in Core.valid_opts}

        return {**conf_opts, **d}


    def cancel_worker(self, tid):
        if tid not in self.worker:
            raise TaskRunningError('task not running')

        del self.worker[tid]


    def load_cmd_args(self, args):
        self.cmd_args['conf'] = args.get('config', None)
        self.cmd_args['host'] = args.get('host', None)
        self.cmd_args['port'] = args.get('port', None)


    def load_conf_file(self):
        with open(self.cmd_args['conf']) as f:
            conf_dict = json.load(f)

        general = conf_dict.get('general', None)
        self.load_general_conf(general)

        server_conf = conf_dict.get('server', None)
        self.load_server_conf(server_conf)

        ydl_opts = conf_dict.get('youtube_dl', None)
        self.load_ydl_conf(ydl_opts)


    def load_general_conf(self, general):
        valid_conf = [  ('download_dir', '/tmp/'),
                        ('db_path', '/tmp/db.db'),
                        ('task_log_size', 10),
                     ]

        general = {} if general is None else general

        for pair in valid_conf:
            self.conf[pair[0]] = general.get(pair[0], pair[1])



    def load_server_conf(self, server_conf):
        valid_conf = [  ('host', '127.0.0.1'),
                        ('port', '5000')
                     ]

        server_conf = {} if server_conf is None else server_conf

        for pair in valid_conf:
            self.conf['server'][pair[0]] = server_conf.get(pair[0], pair[1])


    def load_ydl_conf(self, ydl_opts):
        ydl_opts = {} if ydl_opts is None else ydl_opts

        for opt in Core.valid_opts:
            if opt in ydl_opts:
                self.conf['ydl'][opt] = ydl_opts.get(opt, None)


    def server_request(self, data):
        msg_internal_error = {'status': 'error', 'errmsg': 'Internal Error'}
        msg_task_existence_error = {'status': 'error', 'errmsg': 'URL is already added'}
        msg_task_inexistence_error = {'status': 'error', 'errmsg': 'Task does not exist'}
        if data['command'] == 'create':
            try:
                tid = self.create_task(data['param'], {})
                self.start_task(tid)
            except TaskExistenceError:
                return msg_task_existence_error
            except TaskInexistenceError:
                return msg_internal_error

            return {'status': 'success', 'tid': tid}

        if data['command'] == 'delete':
            try:
                self.delete_task(data['tid'])
            except:
                pass

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


