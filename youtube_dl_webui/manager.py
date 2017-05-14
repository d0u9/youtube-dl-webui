#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from hashlib import sha1
from multiprocessing.managers import BaseManager

from .task import ydl_task, task_desc
from .utils import YDLManagerError
from .utils import TaskError
from .utils import TaskExistenceError, TaskFinishedError, TaskInexistenceError


class share_manager(BaseManager):
    pass


class tasks():
    def __init__(self, conf):
        share_manager.register('task_desc', task_desc)

        # variables
        self._data_ = {}
        self.conf = conf
        self.share_manager = share_manager()
        self.share_manager.start()
        self.conn = self.conf.public.conn
        self.db = self.conf.public.db

        self.load_from_db()


    def load_status_from_db(self, status):
        tasks_dict = {}
        keys = status[0].keys()
        for row in status:
            tid = row['tid']
            tasks_dict[tid] = {}
            tasks_dict[tid]['status'] = {}
            for key in keys:
                tasks_dict[tid]['status'][key] = row[key]

        return tasks_dict


    def load_info_from_db(self, info, tasks_dict):
        keys = info[0].keys()
        for row in info:
            tid = row['tid']
            if tid not in tasks_dict:
                continue
            tasks_dict[tid]['info'] = {}
            for key in keys:
                tasks_dict[tid]['info'][key] = row[key]

        return tasks_dict


    def load_param_from_db(self, param, tasks_dict):
        keys = param[0].keys()
        for row in param:
            tid = row['tid']
            if tid not in tasks_dict:
                continue
            tasks_dict[tid]['param'] = {}
            for key in keys:
                tasks_dict[tid]['param'][key] = row[key]

        return tasks_dict


    def load_param_from_db(self, ydl_opt, tasks_dict):
        for row in ydl_opt:
            tid = row['tid']
            if tid not in tasks_dict:
                continue
            tasks_dict[tid]['ydl_opt'] = json.loads(row['opt'])

        return tasks_dict


    def load_from_db(self):
        self.db.execute('SELECT * FROM task_status WHERE state!=?', (task_desc.state_index['finished'], ))
        status = self.db.fetchall()
        if status is None or len(status) is 0:
            return
        tasks_dict = self.load_status_from_db(status)

        self.db.execute('SELECT * FROM task_info')
        info = self.db.fetchall()
        if info is None:
            return
        tasks_dict = self.load_info_from_db(info, tasks_dict)

        self.db.execute('SELECT * FROM task_param')
        param = self.db.fetchall()
        if param is None:
            return
        tasks_dict = self.load_param_from_db(param, tasks_dict)

        self.db.execute('SELECT * FROM task_ydl_opt')
        ydl_opt = self.db.fetchall()
        if ydl_opt is None:
            return
        tasks_dict = self.load_ydl_opt_from_db(ydl_opt, tasks_dict)

        for tid, val in tasks_dict.items():
            self._data_[tid] = {}
            self.add_param(tid, val['param'])
            desc = self.add_desc(tid)
            desc.load_from_db_dict(val)
            task = ydl_task(val['param'], desc, val['ydl_opt'])
            self.add_object(tid, task)


    def create_task(self, param):
        if 'url' not in param:
            print ('[ERROR] Can not find url in task param')
            raise TaskError('No url in task parameters')


        url = param.get('url')
        tid =  sha1(url.encode()).hexdigest()

        if tid in self._data_:
            raise TaskExistenceError('Task already exists', url=url)

        self._data_[tid] = {}

        self.add_param(tid, param)
        desc = self.add_desc(tid)
        ydl_opts = self.conf.ydl_opts
        task = ydl_task(param, desc, ydl_opts)
        self.add_object(tid, task)

        return tid


    def add_param(self, tid, param):
        # Combine default config with the current task param
        pass

        param['tid'] = tid
        self._data_[tid]['param'] = param
        self._data_[tid]['desc'] = None


    def get_param(self, tid):
        if tid not in self._data_:
            raise TaskInexistenceError('Task does not exist', tid=tid)

        return self._data_.get(tid).get('param')


    def add_desc(self, tid):
        url = self._data_[tid]['param']['url']
        opts = {'log_size': self.conf.dl_log_size}

        self._data_[tid]['desc'] = self.share_manager.task_desc(url, opts)

        return self._data_[tid]['desc']


    def get_desc(self, tid):
        if tid not in self._data_:
            raise TaskInexistenceError('Task does not exist', tid=tid)

        return self._data_.get(tid).get('desc')


    def add_object(self, tid, task):
        self._data_[tid]['object'] = task


    def get_object(self, tid):
        if tid not in self._data_:
            raise TaskInexistenceError('Task does not exist', tid=tid)

        return self._data_.get(tid).get('object')


    def list_tasks(self, state='all', exerpt=True):
        state_index = {'all': 0, 'downloading': 1, 'paused': 2, 'finished': 3}
        counter = {'downloading': 0, 'paused': 0, 'finished': 0}

        if state not in state_index:
            raise TaskError('Not a valid state', tid=tid)

        task_list = {}
        for key, val in self._data_.items():
            status = val['desc'].get_status()
            cstate = status['state']

            if cstate is state_index['downloading']:
                counter['downloading'] += 1
            elif cstate is state_index['paused']:
                counter['paused'] += 1
            elif cstate is state_index['finished']:
                counter['finished'] += 1

            if state is not 'all' and cstate is not state_index[state]:
                continue

            if exerpt:
                task_list[key] = val['desc'].get_exerpt()
            else:
                task_list[key] = val['desc'].get_status()

        return task_list, counter


    def query_task(self, tid, exerpt=False):
        if tid not in self._data_:
            raise TaskInexistenceError('Task does not exist', tid=tid)

        if exerpt:
            return self._data_.get(tid).get('desc').get_exerpt()

        status = self._data_.get(tid).get('desc').get_status()

        return status


    def delete_task(self, tid):
        if tid not in self._data_:
            raise TaskInexistenceError('Task does not exist', tid=tid)

        task = self._data_.pop(tid)
        desc = task.get('desc')
        return desc


class ydl_manger():
    def __init__(self, conf=None):
        self.conf = None
        self.tasks = None
        if conf is not None:
            self.load_conf(conf)


    def load_conf(self, conf):
        self.conf = conf
        os.chdir(self.conf.public.download_dir)

        self.tasks = tasks(self.conf)
        self.conn, self.db = conf.public.get_sqlite_handler()


    def create_task(self, task_param):
        try:
            tid = self.tasks.create_task(task_param)
        except TaskError as e:
            raise YDLManagerError(e.msg)

        return tid


    def start_task(self, tid):
        try:
            task = self.tasks.get_object(tid)
        except TaskError as e:
            raise YDLManagerError(e.msg)

        task.start_dl()


    def pause_task(self, tid):
        try:
            task = self.tasks.get_object(tid)
        except TaskError as e:
            raise YDLManagerError(e.msg)
        task.pause_dl()


    def resume_task(self, tid):
        try:
            task = self.tasks.get_object(tid)
            desc = self.tasks.get_desc(tid)
        except TaskError as e:
            raise YDLManagerError(e.msg)

        if desc.get_status_item('state') is task_desc.state_index['finished']:
            raise YDLManagerError('Already finished', tid=tid)

        task.resume_dl()


    def delete_task(self, tid, del_data=False):
        try:
            self.pause_task(tid)
            desc = self.tasks.delete_task(tid)
        except TaskError as e:
            raise YDLManagerError(e.msg)

        if desc.get_status_item('state') == 'finished':
            file_name = desc.get_item('filename')
        else:
            file_name = desc.get_item('tmpfilename')

        if del_data is True:
            try:
                os.remove(file_name)
            except FileNotFoundError:
                pass


    def list_tasks(self, state='all', exerpt=True):
        try:
            tasks, counter = self.tasks.list_tasks(state=state, exerpt=exerpt)
        except TaskError as e:
            raise YDLManagerError(e.msg)

        return {'tasks': tasks, 'counter': counter}


    def query_task(self, tid, exerpt=False):
        try:
            task = self.tasks.get_object(tid)
        except TaskError as e:
            raise YDLManagerError(e.msg)

        return self.tasks.query_task(tid, exerpt)


    def state_list(self):
        tasks, counter = self.tasks.list_tasks(state='all', exerpt=True)
        return counter

