#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
from time import sleep

def task_add(url):
    r = requests.post('http://127.0.0.1:5000/task', data={'url': url})
    print('status: {}'.format(r.status_code))
    j = json.loads(r.text)
    return j


def task_act(tid, act):
    url = 'http://127.0.0.1:5000/task/{}?act={}'.format(tid, act)
    if act is 'pause' or act is 'resume':
        r = requests.put(url)
        print('status: {}'.format(r.status_code))
        j = json.loads(r.text)

    return j


def task_delete(tid, del_data=False):
    url = 'http://127.0.0.1:5000/task/{}'.format(tid)

    r = requests.delete(url)

    print('status: {}'.format(r.status_code))
    j = json.loads(r.text)

    return j


def task_query(tid, exerpt=False):
    url = 'http://127.0.0.1:5000/task/{}/status'.format(tid)

    if exerpt is True:
        url = url + '?exerpt=true'

    r = requests.get(url)
    print('status: {}'.format(r.status_code))
    j = json.loads(r.text)
    return j


if __name__ == '__main__':
    print('add a new task')
    r = task_add('test url')
    tid = r['tid']
    print(r)
    sleep(1)

    print('--------- get status')
    r = task_query(tid)
    print (r)
    sleep(1)

    print('--------- pause a task')
    r = task_act(tid, 'pause')
    print(r)
    sleep(2)

    print('--------- resume a task')
    r = task_act(tid, 'resume')
    print(r)

    print('--------- get status')
    r = task_query(tid, True)
    print (r)
    sleep(1)

    sleep(3)
    print('--------- delete a task')
    r = task_delete(tid)

