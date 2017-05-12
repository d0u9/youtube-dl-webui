#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from hashlib import sha1
from multiprocessing.managers import BaseManager

from .task import ydl_task, task_desc
from .utils import TaskError
from .utils import YDLManagerError


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


    def add_param(self, param):
        if 'url' not in param:
            print ('[ERROR] Can not find url in task param')
            raise TaskError('No url in task parameters')

        # Combine default config with the current task param
        pass

        url = param.get('url')
        tid =  sha1(url.encode()).hexdigest()

        if tid in self._data_:
            raise TaskError('Task exists', url=url)

        param['tid'] = tid
        self._data_[tid] = {}
        self._data_[tid]['param'] = param
        self._data_[tid]['desc'] = None

        return tid


    def get_param(self, tid):
        if tid not in self._data_:
            raise TaskError('Task does not exist', tid=tid)

        return self._data_.get(tid).get('param')


    def add_desc(self, tid):
        if tid not in self._data_:
            raise TaskError('Task does not exist', tid=tid)

        url = self._data_[tid]['param']['url']
        opts = {'log_size': self.conf.dl_log_size}

        self._data_[tid]['desc'] = self.share_manager.task_desc(url, opts)


    def get_desc(self, tid):
        if tid not in self._data_:
            raise TaskError('Task does not exist', tid=tid)

        return self._data_.get(tid).get('desc')


    def add_object(self, tid, task):
        if tid not in self._data_:
            raise TaskError('Task does not exist', tid=tid)

        self._data_[tid]['object'] = task


    def get_object(self, tid):
        if tid not in self._data_:
            raise TaskError('Task does not exist', tid=tid)

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
            raise TaskError('Task does not exist', tid=tid)

        if exerpt:
            return self._data_.get(tid).get('desc').get_exerpt()

        status = self._data_.get(tid).get('desc').get_status()

        return status


    def delete_task(self, tid):
        if tid not in self._data_:
            raise TaskError('Task does not exist', tid=tid)

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


    def create_task(self, task_param):
        try:
            tid = self.tasks.add_param(task_param)
        except TaskError as e:
            raise YDLManagerError(e.msg)

        self.tasks.add_desc(tid)

        param = task_param
        desc = self.tasks.get_desc(tid)
        ydl_opts = self.conf.ydl_opts
        task = ydl_task(param, desc, ydl_opts)

        self.tasks.add_object(tid, task)

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
        except TaskError as e:
            raise YDLManagerError(e.msg)
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

