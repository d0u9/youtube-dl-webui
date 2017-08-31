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

from .config import ydl_conf, conf
from .task import TaskManager, Task


def load_conf_from_file(cmd_args):
    logger = logging.getLogger('ydl_webui')

    conf_file = cmd_args.get('config', None)
    logger.info('load config file (%s)' %(conf_file))

    if cmd_args is None or conf_file is None:
        return ({}, {})

    try:
        with open(expanduser(conf_file)) as f:
            return (json.load(f), cmd_args)
    except FileNotFoundError as e:
        logger.critical("Config file (%s) doesn't exist", conf_file)
        exit(1)


class Core(object):
    exerpt_keys = ['tid', 'state', 'percent', 'total_bytes', 'title', 'eta', 'speed']

    def __init__(self, cmd_args=None):
        self.logger = logging.getLogger('ydl_webui')

        self.logger.debug('cmd_args = %s' %(cmd_args))
        conf_dict, cmd_args = load_conf_from_file(cmd_args)
        self.conf = conf(conf_dict=conf_dict, cmd_args=cmd_args)

        self.db = DataBase(self.conf['general']['db_path'])
        self.task_manager = TaskManager(self.db)

        #  tid = self.task_manager.new_task('ix212xx', {'proxy': '12.12.12.12'})
        #  self.task_manager.start_task(tid)

        #  exit(1)

        self.rq = Queue()
        self.wq = Queue()
        self.worker = {}

        self.logger.debug("configuration: \n%s", json.dumps(self.conf.dict(), indent=4))

        self.server = Server(self.wq, self.rq, self.conf['server']['host'], self.conf['server']['port'])
        self.db = DataBase(self.conf['general']['db_path'])

        dl_dir = self.conf['general']['download_dir']
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

        opts = {}
        for key, val in self.conf['ydl'].items():
            if key in ydl_opts:
                opts[key] = ydl_opts[key]
            else:
                opts[key] = self.conf['ydl'][key]

        tid = self.db.create_task(param, opts)
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


    def delete_task(self, tid, del_data=False):
        try:
            self.cancel_worker(tid)
        except TaskInexistenceError as e:
            raise e
        except:
            pass

        self.db.delete_task(tid, del_data=del_data)


    def launch_worker(self, tid, log_list, param=None, ydl_opts={}, first_run=False):
        if tid in self.worker:
            raise TaskRunningError('task already running')

        self.worker[tid] ={'obj': None, 'log': deque(maxlen=10)}

        for l in log_list:
            self.worker[tid]['log'].appendleft(l)

        self.worker[tid]['log'].appendleft({'time': int(time()), 'type': 'debug', 'msg': 'Task starts...'})
        self.db.update_log(tid, self.worker[tid]['log'])

        self.logger.debug("ydl_opts(%s): %s" %(tid, json.dumps(ydl_opts)))

        # launch worker process
        w = Worker(tid, self.rq, param=param, ydl_opts=ydl_opts, first_run=first_run)
        w.start()
        self.worker[tid]['obj'] = w


    def cancel_worker(self, tid):
        if tid not in self.worker:
            raise TaskPausedError('task not running')

        w = self.worker[tid]
        self.db.cancel_task(tid, log=w['log'])
        w['obj'].stop()
        self.worker[tid]['log'].appendleft({'time': int(time()), 'type': 'debug', 'msg': 'Task stops...'})
        self.db.update_log(tid, self.worker[tid]['log'])

        del self.worker[tid]


    def cmdl_override_conf_file(self):
        if self.cmdl_args_dict['host'] is not None:
            self.conf['server']['host'] = self.cmdl_args_dict['host']

        if self.cmdl_args_dict['port'] is not None:
            self.conf['server']['port'] = self.cmdl_args_dict['port']


    def update_config(self, config):
        print(config)


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
                self.delete_task(data['tid'], del_data=data['del_data'])
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

        if data['command'] == 'config':
            if data['act'] == 'get':
                return {'status': 'success', 'config': self.conf}
            elif data['act'] == 'update':
                self.update_config(data['param'])
                return {'status': 'success'}
            else:
                return {'status': 'error', 'errmsg': 'invalid query'}


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

