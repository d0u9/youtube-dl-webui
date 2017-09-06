#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os

from time import time

from .config import ydl_conf
from .utils import TaskInexistenceError
from .utils import TaskRunningError
from .utils import TaskExistenceError
from .utils import TaskPausedError
from .utils import url2tid

class Task(object):

    def __init__(self, tid, ydl_opts={}, info={}, status={}):
        self.tid = tid
        self.ydl_conf = ydl_conf(ydl_opts)
        self.info = info
        self.status = status

    def start(self):
        self.start_time = time()
        print('---- task  start ----')

    def pause(self):
        self.pause_time = time()
        print('---- task  pause ----')

    def halt(self):
        self.pause_time = time()
        self.finish_time = time()
        print('---- task  halt ----')

    def finish(self):
        self.pause_time = time()
        self.finish_time = time()
        print('---- task  finish ----')
        pass


class TaskManager(object):
    """
    Tasks are categorized into two types, active type and inactive type.

    Tasks in active type are which in downloading, pausing state. These tasks
    associate with a Task instance in memory. However, inactive type tasks
    are in invalid state or finished state, which only have database recoards
    but memory instance.
    """
    ExerptKeys = ['tid', 'state', 'percent', 'total_bytes', 'title', 'eta', 'speed']

    def __init__(self, db, msg_cli):
        self.logger = logging.getLogger('ydl_webui')
        self._db = db
        self._msg_cli = msg_cli

        self._tasks_dict = {}

    def new_task(self, url, ydl_opts={}):
        """Create a new task and put it in inactive type"""

        return self._db.new_task(url, ydl_opts)

    def start_task(self, tid, ignore_state=False, first_run=False):
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

            task = Task(tid, ydl_opts=ydl_opts, info=info, status=status)
            self._tasks_dict[tid] = task

        task.start()
        self._db.start_task(tid, start_time=task.start_time)

        return task

    def pause_task(self, tid):
        self.logger.debug('task paused (%s)' %(tid))

        if tid not in self._tasks_dict:
            raise TaskInexistenceError

        task = self._tasks_dict[tid]
        task.pause()
        elapsed = task.pause_time - task.start_time + task.status['elapsed']
        self._db.pause_task(tid, pause_time=task.pause_time, elapsed=elapsed)

    def finish_task(self, tid):
        self.logger.debug('task finished (%s)' %(tid))

        if tid not in self._tasks_dict:
            raise TaskInexistenceError

        task = self._tasks_dict[tid]
        del self._tasks_dict[tid]
        task.finish()
        elapsed = task.finish_time - task.start_time + task.status['elapsed']
        self._db.finish_task(tid, finish_time=task.finish_time, elapsed=elapsed)

    def halt_task(self, tid):
        self.logger.debug('task halted (%s)' %(tid))

        if tid not in self._tasks_dict:
            raise TaskInexistenceError

        task = self._tasks_dict[tid]
        del self._tasks_dict[tid]
        task.halt()
        elapsed = task.finish_time - task.start_time + task.status['elapsed']
        self._db.halt_task(tid, finish_time=task.halt_time, elapsed=elapsed)

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
            os.remove(dl_file)

    def query(self, tid, exerpt=True):
        db_ret = self._db.query_task(tid)

        detail = {}
        if exerpt:
            detail = {k: db_ret[k] for k in ret if k in self.ExerptKeys}
        else:
            detail = db_ret

        return detail

