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
from .utils import TaskExistenceError
from .utils import TaskError
from .server import Server
from .worker import Worker

from .config import ydl_conf, conf
from .task import TaskManager, Task
from .msg import MsgMgr

class WebMsgDispatcher(object):
    logger = logging.getLogger('ydl_webui')

    SuccessMsg              = {'status': 'success'}
    InternalErrorMsg        = {'status': 'error', 'errmsg': 'Internal Error'}
    TaskExistenceErrorMsg   = {'status': 'error', 'errmsg': 'URL is already added'}
    TaskInexistenceErrorMsg = {'status': 'error', 'errmsg': 'Task does not exist'}
    UrlErrorMsg             = {'status': 'error', 'errmsg': 'URL is invalid'}
    InvalidStateMsg         = {'status': 'error', 'errmsg': 'Invalid query state'}
    RequestErrorMsg         = {'status': 'error', 'errmsg': 'Request error'}

    _task_mgr = None
    _conf = None

    @classmethod
    def init(cls, conf, task_mgr):
        cls._task_mgr = task_mgr
        cls._conf = conf

    @classmethod
    def event_create(cls, svr, event, data, args):
        url, ydl_opts = data.get('url', None), data.get('ydl_opts', {})
        cls.logger.debug('url = %s, ydl_opts = %s' %(url, ydl_opts))

        if url is None:
            svr.put(cls.UrlErrorMsg)
            return

        try:
            tid = cls._task_mgr.new_task(url, ydl_opts=ydl_opts)
        except TaskExistenceError:
            svr.put(cls.TaskExistenceErrorMsg)
            return

        task = cls._task_mgr.start_task(tid)

        svr.put({'status': 'success', 'tid': tid})

    @classmethod
    def event_delete(cls, svr, event, data, args):
        tid, del_file = data['tid'], data['del_file']

        try:
            cls._task_mgr.delete_task(tid, del_file)
        except TaskInexistenceError:
            svr.put(cls.TaskInexistenceErrorMsg)
        else:
            svr.put(cls.SuccessMsg)

    @classmethod
    def event_manipulation(cls, svr, event, data, args):
        cls.logger.debug('manipulation event')
        tid, act = data['tid'], data['act']

        ret_val = cls.RequestErrorMsg
        if   act == 'pause':
            try:
                cls._task_mgr.pause_task(tid)
            except TaskError as e:
                ret_val = {'status': 'error', 'errmsg': e.msg}
            else:
                ret_val = cls.SuccessMsg
        elif act == 'resume':
            try:
                cls._task_mgr.start_task(tid)
            except TaskError as e:
                ret_val = {'status': 'error', 'errmsg': e.msg}
            else:
                ret_val = cls.SuccessMsg

        svr.put(ret_val)

    @classmethod
    def event_query(cls, svr, event, data, args):
        cls.logger.debug('query event')
        tid, exerpt = data['tid'], data['exerpt']

        try:
            detail = cls._task_mgr.query(tid, exerpt)
        except TaskInexistenceError:
            svr.put(cls.TaskInexistenceErrorMsg)
        else:
            svr.put({'status': 'success', 'detail': detail})

    @classmethod
    def event_list(cls, svr, event, data, args):
        exerpt, state = data['exerpt'], data['state']

        if state not in state_name:
            svr.put(cls.InvalidStateMsg)
        else:
            d, c = cls._task_mgr.list(state, exerpt)
            svr.put({'status': 'success', 'detail': d, 'state_counter': c})

    @classmethod
    def event_state(cls, svr, event, data, args):
        c = cls._task_mgr.state()
        svr.put({'status': 'success', 'detail': c})

    @classmethod
    def event_config(cls, svr, event, data, arg):
        act = data['act']

        ret_val = cls.RequestErrorMsg
        if   act == 'get':
            ret_val = {'status': 'success'}
            ret_val['config'] = cls._conf.dict()
        elif act == 'update':
            conf_dict = data['param']
            cls._conf.load(conf_dict)
            suc, msg = cls._conf.save2file()
            if suc:
                ret_val = cls.SuccessMsg
            else:
                ret_val = {'status': 'error', 'errmsg': msg}

        svr.put(ret_val)

    @classmethod
    def event_batch(cls, svr, event, data, arg):
        act, detail = data['act'], data['detail']

        if 'tids' not in detail:
            svr.put(cls.RequestErrorMsg)
            return

        tids = detail['tids']
        errors = []
        if   act == 'pause':
            for tid in tids:
                try:
                    cls._task_mgr.pause_task(tid)
                except TaskInexistenceError:
                    errors.append([tid, 'Inexistence error'])
                except TaskError as e:
                    errors.append([tid, e.msg])
        elif act == 'resume':
            for tid in tids:
                try:
                    cls._task_mgr.start_task(tid)
                except TaskInexistenceError:
                    errors.append([tid, 'Inexistence error'])
                except TaskError as e:
                    errors.append([tid, e.msg])
        elif act == 'delete':
            del_file = True if detail.get('del_file', 'false') == 'true' else False
            for tid in tids:
                try:
                    cls._task_mgr.delete_task(tid, del_file)
                except TaskInexistenceError:
                    errors.append([tid, 'Inexistence error'])

        if errors:
            ret_val = {'status': 'success', 'detail': errors}
        else:
            ret_val = cls.SuccessMsg

        svr.put(ret_val)


class WorkMsgDispatcher(object):

    _task_mgr = None
    logger = logging.getLogger('ydl_webui')

    @classmethod
    def init(cls, task_mgr):
        cls._task_mgr = task_mgr

    @classmethod
    def event_info_dict(cls, svr, event, data, arg):
        tid, info_dict = data['tid'], data['data']
        cls._task_mgr.update_info(tid, info_dict)

    @classmethod
    def event_log(cls, svr, event, data, arg):
        tid, log = data['tid'], data['data']
        cls._task_mgr.update_log(tid, log)

    @classmethod
    def event_fatal(cls, svr, event, data, arg):
        tid, data = data['tid'], data['data']

        cls._task_mgr.update_log(tid, data)
        if data['type'] == 'fatal':
            cls._task_mgr.halt_task(tid)

    @classmethod
    def event_progress(cls, svr, event, data, arg):
        tid, data = data['tid'], data['data']
        try:
            cls._task_mgr.progress_update(tid, data)
        except TaskInexistenceError:
            cls.logger.error('Cannot update progress, task does not exist')

    @classmethod
    def event_worker_done(cls, svr, event, data, arg):
        tid, data = data['tid'], data['data']
        try:
            cls._task_mgr.finish_task(tid)
        except TaskInexistenceError:
            cls.logger.error('Cannot finish, task does not exist')


def load_conf_from_file(cmd_args):
    logger = logging.getLogger('ydl_webui')

    conf_file = cmd_args.get('config', None)
    logger.info('load config file (%s)' %(conf_file))

    if cmd_args is None or conf_file is None:
        return (None, {}, {})

    abs_file = os.path.abspath(conf_file)
    try:
        with open(abs_file) as f:
            return (abs_file, json.load(f), cmd_args)
    except FileNotFoundError as e:
        logger.critical("Config file (%s) doesn't exist", conf_file)
        exit(1)


class Core(object):
    exerpt_keys = ['tid', 'state', 'percent', 'total_bytes', 'title', 'eta', 'speed']

    def __init__(self, cmd_args=None):
        self.logger = logging.getLogger('ydl_webui')

        self.logger.debug('cmd_args = %s' %(cmd_args))

        conf_file, conf_dict, cmd_args = load_conf_from_file(cmd_args)
        self.conf = conf(conf_file, conf_dict=conf_dict, cmd_args=cmd_args)
        self.logger.debug("configuration: \n%s", json.dumps(self.conf.dict(), indent=4))

        self.msg_mgr = MsgMgr()
        web_cli  = self.msg_mgr.new_cli('server')
        task_cli = self.msg_mgr.new_cli()

        self.db = DataBase(self.conf['general']['db_path'])
        self.task_mgr = TaskManager(self.db, task_cli, self.conf)

        WebMsgDispatcher.init(self.conf, self.task_mgr)
        WorkMsgDispatcher.init(self.task_mgr)

        self.msg_mgr.reg_event('create',     WebMsgDispatcher.event_create)
        self.msg_mgr.reg_event('delete',     WebMsgDispatcher.event_delete)
        self.msg_mgr.reg_event('manipulate', WebMsgDispatcher.event_manipulation)
        self.msg_mgr.reg_event('query',      WebMsgDispatcher.event_query)
        self.msg_mgr.reg_event('list',       WebMsgDispatcher.event_list)
        self.msg_mgr.reg_event('state',      WebMsgDispatcher.event_state)
        self.msg_mgr.reg_event('config',     WebMsgDispatcher.event_config)
        self.msg_mgr.reg_event('batch',      WebMsgDispatcher.event_batch)

        self.msg_mgr.reg_event('info_dict',  WorkMsgDispatcher.event_info_dict)
        self.msg_mgr.reg_event('log',        WorkMsgDispatcher.event_log)
        self.msg_mgr.reg_event('progress',   WorkMsgDispatcher.event_progress)
        self.msg_mgr.reg_event('fatal',      WorkMsgDispatcher.event_fatal)
        self.msg_mgr.reg_event('worker_done',WorkMsgDispatcher.event_worker_done)

        self.server = Server(web_cli, self.conf['server']['host'], self.conf['server']['port'])

    def start(self):
        dl_dir = self.conf['general']['download_dir']
        try:
            os.makedirs(dl_dir, exist_ok=True)
            self.logger.info('Download dir: %s' %(dl_dir))
            os.chdir(dl_dir)
        except PermissionError:
            self.logger.critical('Permission error when accessing download dir')
            exit(1)

        self.task_mgr.launch_unfinished()
        self.server.start()
        self.msg_mgr.run()

