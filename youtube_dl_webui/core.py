#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os

from .db import DataBase
from .utils import TaskInexistenceError
from .utils import TaskRunningError

class Core(object):
    def __init__(self, args=None):
        self.cmd_args = {}
        self.conf = {'server': {}, 'ydl': {}}
        self.worker = {}

        if args is not None:
            self.load_cmd_args(args)

        self.load_conf_file()

        self.db = DataBase(self.conf['db_path'])

        self.launch_unfinished()


    def launch_unfinished(self):
        tlist = self.db.get_unfinished()
        for t in tlist:
            self.start_task(t)


    def create_task(self, param, ydl_opts):
        if 'url' not in param:
            raise KeyError

        self.db.create_task(param, ydl_opts)


    def start_task(self, tid):
        try:
            param = self.db.get_param(tid)
            ydl_opts = self.db.get_opts(tid)
        except TaskInexistenceError as e:
            print('task oops!')
            return

        self.db.start_task(tid)
        self.launch_worker(tid)


    def pause_task(self, tid):
        try:
            self.cancel_worker(tid)
            self.db.pause_task(tid)
        except TaskRunningError as e:
            pass
        except KeyError as e:
            pass


    def delete_task(self, tid):
        self.cancel_worker(tid)
        self.db.delete_task(tid)


    def launch_worker(self, tid):
        print(tid)
        if tid in self.worker:
            raise TaskRunningError('task already running')

        self.worker[tid] = 'worker'


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
        valid_opts = ['proxy']

        ydl_opts = {} if ydl_opts is None else ydl_opts

        for opt in valid_opts:
            if opt in ydl_opts:
                self.conf['ydl'][opt] = ydl_opts.get(opt, None)
