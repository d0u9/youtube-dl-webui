#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import json
import glob

from time import time
from collections import deque

from .config import ydl_conf
from .utils import TaskInexistenceError
from .utils import TaskExistenceError
from .utils import TaskError
from .utils import url2tid
from .utils import state_index

from .worker import Worker

class Task(object):

    def __init__(self, tid, msg_cli, ydl_opts={}, info={}, status={}, log_size=10):
        self.logger = logging.getLogger('ydl_webui')
        self.tid = tid
        self.ydl_opts = ydl_opts
        self.ydl_conf = ydl_conf(ydl_opts)
        self.info = info
        self.url = info['url']
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
        self.logger.info('Task starts, url: %s(%s), ydl_opts: %s' %(self.url, self.tid, self.ydl_opts))
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
        self.logger.info('Task pauses, url - %s(%s)' %(self.url, self.tid))
        tm = time()
        self.state = state_index['paused']

        self.pause_time = tm
        self.elapsed = self.elapsed + (tm - self.touch)
        self.touch = tm

        self.worker.stop()
        self.log.appendleft({'time': int(tm), 'type': 'debug', 'msg': 'Task pauses...'})

    def halt(self):
        self.logger.info('Task halts, url - %s(%s)' %(self.url, self.tid))
        tm = time()
        self.state = state_index['invalid']

        self.halt_time = tm
        self.finish_time = tm
        self.elapsed = self.elapsed + (tm - self.touch)
        self.touch = tm

        self.worker.stop()
        self.log.appendleft({'time': int(tm), 'type': 'debug', 'msg': 'Task halts...'})

    def finish(self):
        self.logger.info('Task finishes, url - %s(%s)' %(self.url, self.tid))
        tm = time()
        self.state = state_index['finished']

        self.pause_time = tm
        self.finish_time = tm
        self.elapsed = self.elapsed + (tm - self.touch)
        self.touch = tm

        self.worker.stop()
        self.log.appendleft({'time': int(tm), 'type': 'debug', 'msg': 'Task finishs...'})

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

        # stripe out necessary fields
        ydl_opts = ydl_conf(ydl_opts)
        return self._db.new_task(url, ydl_opts.dict())

    def start_task(self, tid, ignore_state=False):
        """make an inactive type task into active type"""

        task = None
        if tid in self._tasks_dict:
            task = self._tasks_dict[tid]
            if task.state == state_index['downloading']:
                raise TaskError('Task is downloading')
        else:
            try:
                ydl_opts = self.ydl_conf.merge_conf(self._db.get_ydl_opts(tid))
                info     = self._db.get_info(tid)
                status   = self._db.get_stat(tid)
            except TaskInexistenceError as e:
                raise TaskInexistenceError(e.msg)

            if status['state'] == state_index['finished']:
                raise TaskError('Task is finished')

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
            raise TaskError('Task is finished or invalid or inexistent')

        task = self._tasks_dict[tid]
        if task.state == state_index['paused']:
            raise TaskError('Task already paused')

        task.pause()
        self._db.pause_task(tid, pause_time=task.pause_time, elapsed=task.elapsed)
        self._db.update_log(tid, task.log)

    def finish_task(self, tid):
        self.logger.debug('task finished (%s)' %(tid))

        if tid not in self._tasks_dict:
            raise TaskInexistenceError('task does not exist')

        task = self._tasks_dict[tid]
        task.finish()
        self._db.finish_task(tid, finish_time=task.finish_time, elapsed=task.elapsed)
        self._db.update_log(tid, task.log)
        del self._tasks_dict[tid]

    def halt_task(self, tid):
        self.logger.debug('task halted (%s)' %(tid))

        if tid not in self._tasks_dict:
            raise TaskInexistenceError('task does not exist')

        task = self._tasks_dict[tid]
        task.halt()
        self._db.halt_task(tid, halt_time=task.halt_time, elapsed=task.elapsed)
        self._db.update_log(tid, task.log)
        del self._tasks_dict[tid]

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
            file_wo_ext, ext = dl_file, None
            while ext != '':
                file_wo_ext, ext = os.path.splitext(file_wo_ext)

            for fname in os.listdir(os.getcwd()):
                if fname.startswith(file_wo_ext):
                    self.logger.debug('delete file: %s' %(fname))
                    os.remove(os.path.join(os.getcwd(), fname))

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
            raise TaskInexistenceError('task does not exist')

        task = self._tasks_dict[tid]
        task.update_info(info_dict)

        self._db.update_info(tid, info_dict)

    def update_log(self, tid, log):
        if tid not in self._tasks_dict:
            #  raise TaskInexistenceError('task does not exist')
            self.logger.error('Task does not active, tid=%s' %(tid))
            return

        task = self._tasks_dict[tid]
        task.update_log(log)
        self._db.update_log(tid, task.log, exist_test=False)

    def progress_update(self, tid, data):
        if tid not in self._tasks_dict:
            raise TaskInexistenceError('task does not exist')

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
            try:
                self.start_task(t)
            except TaskError as e:
                self.logger.warn("Task %s is in downloading or finished state", tid)
            except TaskInexistenceError:
                self.logger.error('Task does not exist')

