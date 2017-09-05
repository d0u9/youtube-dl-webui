#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from hashlib import sha1

from .config import ydl_conf
from .utils import TaskInexistenceError
from .utils import TaskRunningError
from .utils import TaskExistenceError
from .utils import TaskPausedError

def url2tid(url):
    return sha1(url.encode()).hexdigest()

class Task(object):

    def __init__(self, tid, ydl_opts={}, info={}, status={}):
        self.tid = tid
        self.ydl_conf = ydl_conf(ydl_opts)
        self.info = info
        self.status = status

    def start(self):
        print('---- task  start ----')

    def pause(self):
        print('---- task  pause ----')

    def halt(self):
        print('---- task  halt ----')

    def finish(self):
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

        if tid in self._tasks_dict:
            task = self._tasks_dict[tid]
            task.start()
            return task

        try:
            ydl_opts = self._db.get_ydl_opts(tid)
            info     = self._db.get_info(tid)
            status   = self._db.get_stat(tid)
        except TaskInexistenceError as e:
            raise TaskInexistenceError(e.msg)

        task = Task(tid, ydl_opts=ydl_opts, info=info, status=status)
        self._tasks_dict[tid] = task

        task.start()

        return task

    def pause_task(self, tid):
        self.logger.debug('task paused (%s)' %(tid))
        task = self._tasks_dict[tid]
        task.pause()

    def halt_task(self, tid):
        self.logger.debug('task halted (%s)' %(tid))

        if tid in self._tasks_dict:
            task = self._tasks_dict[tid]
            task.halt()
            del self._tasks_dict[tid]

    def finish_task(self, tid):
        self.logger.debug('task finished (%s)' %(tid))

        if tid in self._tasks_dict:
            task = self._tasks_dict[tid]
            task.finish()
            del self._tasks_dict[tid]

    def delete_task(self, tid, del_data=False):
        self.logger.debug('task deleted (%s)' %(tid))

        if tid in self._tasks_dict:
            task = self._tasks_dict[tid]
            task.halt()
            del self._tasks_dict[tid]

        if del_data:
            pass
