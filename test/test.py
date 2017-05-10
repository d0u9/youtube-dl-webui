#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
from time import sleep

def task_add(url):
    r = requests.post('http://127.0.0.1:5000/task', data={'url': url})
    print('status: {}'.format(r.status_code))
    j = json.loads(r.text)
    return j['tid']

def task_act(tid, act):
    url = 'http://127.0.0.1:5000/task/{}?act={}'.format(tid, act)
    if act is 'pause' or act is 'resume':
        r = requests.put(url, data={'act': act})
        print('status: {}'.format(r.status_code))
        j = json.loads(r.text)

    return j

if __name__ == '__main__':
    print('add a new task')
    tid = task_add('test url')
    print(tid)
    sleep(1)

    print('--------- pause a task')
    r = task_act(tid, 'pause')
    print(r)
    sleep(3)

    print('--------- resume a task')
    r = task_act(tid, 'resume')
    print(r)

