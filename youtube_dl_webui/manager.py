#!/usr/bin/env python
# -*- coding: utf-8 -*-

from task import ydl_task, task_status

from hashlib import sha1
from multiprocessing.managers import BaseManager

import os

class share_manager(BaseManager):
    pass


class tasks():
    def __init__(self):
        self._data_ = {}
        share_manager.register('task_status', task_status)
        self.share_manager = share_manager()
        self.share_manager.start()


    def add_info(self, info):
        if 'url' not in info:
            print ('[ERROR] Can not find url in task_info')
            return None

        # Combine default config with the current task_info
        pass

        url = info.get('url')
        tid =  sha1(url.encode()).hexdigest()

        info['tid'] = tid
        self._data_[tid] = {}
        self._data_[tid]['info'] = info
        self._data_[tid]['status'] = None

        return tid

    def get_info(self, tid):
        return self._data_.get(tid).get('info')


    def add_status(self, tid):
        url = self._data_[tid]['info']['url']
        self._data_[tid]['status'] = self.share_manager.task_status(url)


    def get_status(self, tid):
        return self._data_.get(tid).get('status')


    def add_object(self, tid, task):
        self._data_[tid]['object'] = task


    def get_object(self, tid):
        return self._data_.get(tid).get('object')


    def enumerate_task(self, state='all', exerpt=False):
        valid_states = {'all': 0, 'downloading': 1, 'paused': 2, 'finished': 3}
        if state not in valid_states:
            return None

        ret = {}
        for key, val in self._data_.items():
            status = val['status'].get_status()

            if state != 'all' and status['state'] != valid_states[state]:
                continue

            if exerpt:
                ret[key] = val['status'].get_exerpt()
            else:
                ret[key] = val['status'].get_status()

        return ret


    def query_task(self, tid, exerpt=False):
        if tid not in self._data_:
            return None

        if exerpt:
            return self._data_.get(tid).get('status').get_exerpt()
        else:
            return self._data_.get(tid).get('status').get_status()


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
    def __init__(self, conf):
        self.conf = conf
        create_dl_dir(self.conf.download_dir)
        os.chdir(self.conf.download_dir)

        # dict to index task, key->url, val->task instance.
        #  share_manager.register('tasks', tasks)
        #  self.share_manager = share_manager()
        #  self.share_manager.start()
        #  self.tasks = self.share_manager.tasks()

        self.tasks = tasks()


    def create_task(self, task_info):
        tid = self.tasks.add_info(task_info)
        self.tasks.add_status(tid)

        #  task = ydl_task(tid, self.tasks, self.conf.ydl_opts)
        info = task_info
        status = self.tasks.get_status(tid)
        ydl_opts = self.conf.ydl_opts
        task = ydl_task(info, status, ydl_opts)
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


    def get_task_status(self, tid):
        s = self.tasks.get_status(tid).get_status()
        return s


    def enumerate_task(self, state='all', exerpt=False):
        return self.tasks.enumerate_task(state=state, exerpt=exerpt)


    def query_task(self, tid, exerpt=False):
        return self.tasks.query_task(tid, exerpt)



