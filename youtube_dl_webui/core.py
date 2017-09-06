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
from .msg import MsgMgr

class WebMsgDispatcher(object):
    logger = logging.getLogger('ydl_webui')

    SuccessMsg              = {'status': 'success'}
    InternalErrorMsg        = {'status': 'error', 'errmsg': 'Internal Error'}
    TaskExistenceErrorMsg   = {'status': 'error', 'errmsg': 'URL is already added'}
    TaskInexistenceErrorMsg = {'status': 'error', 'errmsg': 'Task does not exist'}
    UrlErrorMsg             = {'status': 'error', 'errmsg': 'URL is invalid'}
    InvalidStateMsg         = {'status': 'error', 'errmsg': 'invalid query state'}

    _task_mgr = None

    @classmethod
    def init(cls, task_mgr):
        cls._task_mgr = task_mgr

    @classmethod
    def event_create(cls, svr, event, data, task_mgr):
        cls.logger.debug('url = %s' %(data['url']))
        try:
            tid = task_mgr.new_task(data['url'], {'proxy': '12.12.12.12'})
        except TaskExistenceError:
            svr.put(cls.TaskExistenceErrorMsg)
            return

        task = task_mgr.start_task(tid)

        svr.put({'status': 'success', 'tid': tid})

    @classmethod
    def event_delete(cls, svr, event, data, task_mgr):
        tid = data['tid']
        del_file = True if data['del_file'] == 'true' else False

        try:
            task_mgr.delete_task(tid, del_file)
        except TaskInexistenceError:
            svr.put(cls.TaskInexistenceErrorMsg)
        else:
            svr.put(cls.SuccessMsg)

    @classmethod
    def event_manipulation(cls, svr, event, data, task_mgr):
        cls.logger.debug('manipulation event')
        tid, act = data['tid'], data['act']

        ret_val = cls.InternalErrorMsg
        if   act == 'pause':
            task_mgr.pause_task(tid)
            ret_val = cls.SuccessMsg
        elif act == 'resume':
            task_mgr.start_task(tid)
            ret_val = cls.SuccessMsg

        svr.put(ret_val)

    @classmethod
    def event_query(cls, svr, event, data, task_mgr):
        cls.logger.debug('query event')
        tid, exerpt = data['tid'], data['exerpt']

        try:
            detail = task_mgr.query(tid, exerpt)
        except TaskInexistenceError:
            svr.put(cls.TaskInexistenceErrorMsg)
        else:
            svr.put({'status': 'success', 'detail': detail})

    @classmethod
    def event_list(cls, svr, event, data, task_mgr):
        exerpt, state = data['exerpt'], data['state']

        if state not in state_name:
            svr.put(cls.InvalidStateMsg)
        else:
            d, c = task_mgr.list(state, exerpt)
            svr.put({'status': 'success', 'detail': d, 'state_counter': c})

    @classmethod
    def event_state(cls, svr, event, data, task_mgr):
        c = task_mgr.state()
        svr.put({'status': 'success', 'detail': c})

    @classmethod
    def event_config(cls, svr, event, data, arg):
        svr.put({})


class WorkMsgDispatcher(object):

    def init(cls, __unknow__=None):
        pass


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
        self.logger.debug("configuration: \n%s", json.dumps(self.conf.dict(), indent=4))


        self.msg_mgr = MsgMgr()
        web_cli  = self.msg_mgr.new_cli('server')
        task_cli = self.msg_mgr.new_cli()

        self.db = DataBase(self.conf['general']['db_path'])
        self.task_mgr = TaskManager(self.db, task_cli)

        WebMsgDispatcher.init(self.task_mgr)
        WorkMsgDispatcher.init(self.task_mgr)

        self.msg_mgr.reg_event('create',     WebMsgDispatcher.event_create,     self.task_mgr)
        self.msg_mgr.reg_event('delete',     WebMsgDispatcher.event_delete,     self.task_mgr)
        self.msg_mgr.reg_event('manipulate', WebMsgDispatcher.event_manipulation, self.task_mgr)
        self.msg_mgr.reg_event('query',      WebMsgDispatcher.event_query,      self.task_mgr)
        self.msg_mgr.reg_event('list',       WebMsgDispatcher.event_list,       self.task_mgr)
        self.msg_mgr.reg_event('state',      WebMsgDispatcher.event_state,      self.task_mgr)
        self.msg_mgr.reg_event('config',     WebMsgDispatcher.event_config)

        self.server = Server(web_cli, self.conf['server']['host'], self.conf['server']['port'])

    def start(self):
        self.server.start()
        self.msg_mgr.run()

