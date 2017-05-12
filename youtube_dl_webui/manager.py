#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from hashlib import sha1
from multiprocessing.managers import BaseManager

from .task import ydl_task, task_status

class share_manager(BaseManager):
    pass


class tasks():
    def __init__(self, conf):
        self._data_ = {}
        self.conf = conf
        share_manager.register('task_status', task_status)
        self.share_manager = share_manager()
        self.share_manager.start()


    def add_param(self, param):
        if 'url' not in param:
            print ('[ERROR] Can not find url in task param')
            return None

        # Combine default config with the current task param
        pass

        url = param.get('url')
        tid =  sha1(url.encode()).hexdigest()

        param['tid'] = tid
        self._data_[tid] = {}
        self._data_[tid]['param'] = param
        self._data_[tid]['status'] = None

        return tid


    def get_param(self, tid):
        return self._data_.get(tid).get('param')


    def add_status(self, tid):
        url = self._data_[tid]['param']['url']
        opts = {'log_size': self.conf.dl_log_size}
        self._data_[tid]['status'] = self.share_manager.task_status(url, opts)


    def get_status(self, tid):
        return self._data_.get(tid).get('status')


    def add_object(self, tid, task):
        self._data_[tid]['object'] = task


    def get_object(self, tid):
        return self._data_.get(tid).get('object')


    def list_tasks(self, state='all', exerpt=True):
        state_index = {'all': 0, 'downloading': 1, 'paused': 2, 'finished': 3}
        counter = {'downloading': 0, 'paused': 0, 'finished': 0}

        if state not in state_index:
            return None

        task_list = {}
        for key, val in self._data_.items():
            status = val['status'].get_status()
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
                task_list[key] = val['status'].get_exerpt()
            else:
                task_list[key] = val['status'].get_status()

        return task_list, counter


    def query_task(self, tid, exerpt=False):
        if tid not in self._data_:
            return None

        if exerpt:
            return self._data_.get(tid).get('status').get_exerpt()

        status = self._data_.get(tid).get('status').get_status()

        return status


    def delete_task(self, tid):
        task = self._data_.pop(tid)
        status = task.get('status')
        return status


def create_dl_dir(dl_dir):
    # create download dir
    if os.path.exists(dl_dir) and not os.path.isdir(dl_dir):
        print ('[ERROR] The {} exists, but not a valid directory'.format(dl_dir))
        raise Exception('The download directory is not valid')


    if os.path.exists(dl_dir) and not os.access(dl_dir, os.W_OK | os.X_OK):
        print ('[ERROR] The download directory: {} is not writable'.format(dl_dir))
        raise Exception('The download directory is not writable')

    if not os.path.exists(dl_dir):
        os.makedirs(dl_dir)


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
        tid = self.tasks.add_param(task_param)
        self.tasks.add_status(tid)

        param = task_param
        status = self.tasks.get_status(tid)
        ydl_opts = self.conf.ydl_opts
        task = ydl_task(param, status, ydl_opts)
        self.tasks.add_object(tid, task)

        return tid


    def start_task(self, tid):
        task = self.tasks.get_object(tid)
        task.start_dl()


    def pause_task(self, tid):
        task = self.tasks.get_object(tid)
        task.pause_dl()


    def resume_task(self, tid):
        task = self.tasks.get_object(tid)
        task.resume_dl()


    def delete_task(self, tid, del_data=False):
        state_index = {'downloading': 1, 'paused': 2, 'finished': 3}
        self.pause_task(tid)
        status = self.tasks.delete_task(tid)
        file_name = status.get_item('file')
        state = status.get_item('state')

        if del_data is True:
            os.remove(file_name)


    def get_task_status(self, tid):
        s = self.tasks.get_status(tid).get_status()
        return s


    def list_tasks(self, state='all', exerpt=True):
        tasks, counter = self.tasks.list_tasks(state=state, exerpt=exerpt)

        return {'tasks': tasks, 'counter': counter}


    def query_task(self, tid, exerpt=False):
        return self.tasks.query_task(tid, exerpt)


    def state_list(self):
        tasks, counter = self.tasks.list_tasks(state='all', exerpt=True)
        return counter

