#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import json

from time import time
from collections import deque

from .config import ydl_conf
from .utils import TaskInexistenceError
from .utils import TaskRunningError
from .utils import TaskExistenceError
from .utils import TaskPausedError
from .utils import url2tid
from .utils import state_index

from .worker import Worker

class Task(object):

    def __init__(self, tid, msg_cli, ydl_opts={}, info={}, status={}, log_size=10):
        self.tid = tid
        self.ydl_opts = ydl_opts
        self.ydl_conf = ydl_conf(ydl_opts)
        self.info = info
        self.log = deque(maxlen=log_size)
        self.msg_cli = msg_cli
        self.touch = time()
        self.state = None
        self.elapsed = status['elapsed']
        self.first_run = True if info['valid'] == 0 else False

        log_list = json.loads(status['log'])
        for log in log_list:
            self.log.appendleft(log)

    def start(self):
        print('---- task  start ----')
        tm = time()
        self.state = state_index['downloading']

        self.start_time = tm
        self.elapsed = self.elapsed + (tm - self.touch)
        self.touch = tm

        self.worker = Worker(self.tid, self.info['url'],
                             msg_cli=self.msg_cli,
                             ydl_opts=self.ydl_opts,
                             first_run=self.first_run)
        self.log.appendleft({'time': int(tm), 'type': 'debug', 'msg': 'Task starts...'})
        self.worker.start()

    def pause(self):
        tm = time()
        self.state = state_index['paused']

        self.pause_time = tm
        self.elapsed = self.elapsed + (tm - self.touch)
        self.touch = tm

        self.worker.stop()
        self.log.appendleft({'time': int(tm), 'type': 'debug', 'msg': 'Task pauses...'})
        print('---- task  pause ----')

    def halt(self):
        tm = time()
        self.state = state_index['invalid']

        self.pause_time = tm
        self.finish_time = tm
        self.elapsed = self.elapsed + (tm - self.touch)
        self.touch = tm

        self.worker.stop()
        self.log.appendleft({'time': int(tm), 'type': 'debug', 'msg': 'Task halts...'})
        print('---- task  halt ----')

    def finish(self):
        tm = time()
        self.state = state_index['finished']

        self.pause_time = tm
        self.finish_time = tm
        self.elapsed = self.elapsed + (tm - self.touch)
        self.touch = tm

        self.worker.stop()
        self.log.appendleft({'time': int(tm), 'type': 'debug', 'msg': 'Task finishs...'})
        print('---- task  finish ----')

    def update_info(self, info_dict):
        self.first_run = False

    def update_log(self, log):
        self.log.appendleft(log)

    def progress_update(self, data):
        tm = time()
        self.elapsed = self.elapsed + (tm - self.touch)
        self.touch = tm


class TaskManager(object):
    """
    Tasks are categorized into two types, active type and inactive type.

    Tasks in active type are which in downloading, pausing state. These tasks
    associate with a Task instance in memory. However, inactive type tasks
    are in invalid state or finished state, which only have database recoards
    but memory instance.
    """
    ExerptKeys = ['tid', 'state', 'percent', 'total_bytes', 'title', 'eta', 'speed']

    def __init__(self, db, msg_cli, conf):
        self.logger = logging.getLogger('ydl_webui')
        self._db = db
        self._msg_cli = msg_cli
        self._conf = conf
        self.ydl_conf = conf['youtube_dl']

        self._tasks_dict = {}

    def new_task(self, url, ydl_opts={}):
        """Create a new task and put it in inactive type"""

        return self._db.new_task(url, ydl_opts)

    def start_task(self, tid, ignore_state=False):
        """make an inactive type task into active type"""

        task = None
        if tid in self._tasks_dict:
            task = self._tasks_dict[tid]
        else:
            try:
                ydl_opts = self._db.get_ydl_opts(tid)
                info     = self._db.get_info(tid)
                status   = self._db.get_stat(tid)
            except TaskInexistenceError as e:
                raise TaskInexistenceError(e.msg)

            task = Task(tid, self._msg_cli, ydl_opts=ydl_opts, info=info, 
                        status=status, log_size=self._conf['general']['log_size'])
            self._tasks_dict[tid] = task

        task.start()
        self._db.start_task(tid, start_time=task.start_time)
        self._db.update_log(tid, task.log)

        return task

    def pause_task(self, tid):
        self.logger.debug('task paused (%s)' %(tid))

        if tid not in self._tasks_dict:
            raise TaskInexistenceError

        task = self._tasks_dict[tid]
        task.pause()
        self._db.pause_task(tid, pause_time=task.pause_time, elapsed=task.elapsed)
        self._db.update_log(tid, task.log)

    def finish_task(self, tid):
        self.logger.debug('task finished (%s)' %(tid))

        if tid not in self._tasks_dict:
            raise TaskInexistenceError

        task = self._tasks_dict[tid]
        del self._tasks_dict[tid]
        task.finish()
        self._db.finish_task(tid, finish_time=task.finish_time, elapsed=task.elapsed)
        self._db.update_log(tid, task.log)

    def halt_task(self, tid):
        self.logger.debug('task halted (%s)' %(tid))

        if tid not in self._tasks_dict:
            raise TaskInexistenceError

        task = self._tasks_dict[tid]
        del self._tasks_dict[tid]
        task.halt()
        self._db.halt_task(tid, finish_time=task.halt_time, elapsed=task.elapsed)
        self._db.update_log(tid, task.log)

    def delete_task(self, tid, del_file=False):
        self.logger.debug('task deleted (%s)' %(tid))

        if tid in self._tasks_dict:
            task = self._tasks_dict[tid]
            del self._tasks_dict[tid]
            task.halt()

        try:
            dl_file = self._db.delete_task(tid)
        except TaskInexistenceError as e:
            raise TaskInexistenceError(e.msg)

        if del_file and dl_file is not None:
            abs_dl_file = os.path.join(os.getcwd(), dl_file)
            self.logger.debug('delete file: %s' %(abs_dl_file))
            os.remove(abs_dl_file)

    def query(self, tid, exerpt=True):
        db_ret = self._db.query_task(tid)

        detail = {}
        if exerpt:
            detail = {k: db_ret[k] for k in ret if k in self.ExerptKeys}
        else:
            detail = db_ret

        return detail

    def list(self, state, exerpt=False):
        db_ret, counter = self._db.list_task(state)

        detail = []
        if exerpt is not True:
            for item in db_ret:
                d = {k: item[k] for k in item if k in self.ExerptKeys}
                detail.append(d)
        else:
            detail = db_ret

        return detail, counter

    def state(self):
        return self._db.state_counter()

    def update_info(self, tid, info_dict):
        if tid not in self._tasks_dict:
            raise TaskInexistenceError
        task = self._tasks_dict[tid]
        task.update_info(info_dict)

        self._db.update_info(tid, info_dict)

    def update_log(self, tid, log):
        if tid not in self._tasks_dict:
            raise TaskInexistenceError

        task = self._tasks_dict[tid]
        task.update_log(log)
        self._db.update_log(tid, task.log, exist_test=False)

    def progress_update(self, tid, data):
        if tid not in self._tasks_dict:
            raise TaskInexistenceError
        task = self._tasks_dict[tid]
        task.progress_update(data)

        if 'total_bytes' in data:
            data['total_bytes_estmt'] = data['total_bytes']
        else:
            data['total_bytes'] = '0'

        self._db.progress_update(tid, data, task.elapsed)

    def launch_unfinished(self):
        tid_list = self._db.launch_unfinished()

        for t in tid_list:
            self.start_task(t)

