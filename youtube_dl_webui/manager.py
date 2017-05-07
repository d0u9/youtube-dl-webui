#!/usr/bin/env python
# -*- coding: utf-8 -*-

from task import ydl_task
from hashlib import sha1

import os

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
        # dict to index task, key->url, val->task instance.
        self.workers = {}

        self.conf = conf

        create_dl_dir(self.conf.download_dir)
        os.chdir(self.conf.download_dir)


    def create_task(self, task_info):
        if 'url' not in task_info:
            print ('[ERROR] Can not find url in task_info')
            return False

        url = task_info.get('url')
        task_info['id'] = sha1(url.encode()).hexdigest()

        # Combine default config with the current task_info
        pass

        task = ydl_task(task_info, self.conf.ydl_conf.dict())
        self.workers[id] = task

        task.start_dl()
        import time
        time.sleep(10)
        task.stop_dl()

        return True


if __name__ == '__main__':
    T = ydl_manager()

    params = {'url': 'https://www.youtube.com/watch?v=daVDrGsaDME'}
    t = T.create_worker(params)
    t.test()
    t.start_dl()

    params = {'url': 'https://www.youtube.com/watch?v=YsCFDBJLd2M'}
    t = T.create_worker(params)
    t.test()
    t.start_dl()





