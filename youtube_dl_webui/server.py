#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from flask import Flask
from flask import render_template
from flask import request
from multiprocessing import Process
from copy import deepcopy

app = Flask(__name__)

RQ = None
WQ = None

WQ_DICT = {'from': 'server'}
MSG_INVALID_REQUEST = {'status': 'error', 'errmsg': 'invalid request'}

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/task', methods=['POST'])
def add_task():
    wqd = deepcopy(WQ_DICT)
    wqd['command'] = 'create'
    wqd['param'] = {'url': request.form['url']}
    wqd['ydl_opts'] = {}

    WQ.put(wqd)
    return json.dumps(RQ.get())


@app.route('/task/list', methods=['GET'])
def list_task():
    wqd = deepcopy(WQ_DICT)
    wqd['command'] = 'list'

    exerpt = request.args.get('exerpt', None)

    if exerpt is None:
        wqd['exerpt'] = True
    else:
        wqd['exerpt'] = False

    WQ.put(wqd)
    return json.dumps(RQ.get())


@app.route('/task/state_counter', methods=['GET'])
def list_state():
    pass


@app.route('/task/tid/<tid>', methods=['DELETE'])
def delete_task(tid):
    wqd = deepcopy(WQ_DICT)
    wqd['command'] = 'delete'
    wqd['tid'] = tid

    WQ.put(wqd)
    return json.dumps(RQ.get())


@app.route('/task/tid/<tid>', methods=['PUT'])
def manipulate_task(tid):
    wqd = deepcopy(WQ_DICT)
    wqd['command'] = 'manipulate'
    wqd['tid'] = tid

    act = request.args.get('act', None)

    if act == 'pause':
        wqd['act'] = 'pause'
    elif act == 'resume':
        wqd['act'] = 'resume'
    else:
        return json.dumps(MSG_INVALID_REQUEST)

    WQ.put(wqd)
    return json.dumps(RQ.get())


@app.route('/task/tid/<tid>/status', methods=['GET'])
def query_task(tid):
    wqd = deepcopy(WQ_DICT)
    wqd['command'] = 'query'
    wqd['tid'] = tid

    exerpt = request.args.get('exerpt', None)

    if exerpt is None:
        wqd['exerpt'] = False
    else:
        wqd['exerpt'] = True

    WQ.put(wqd)
    return json.dumps(RQ.get())



class Server(Process):
    def __init__(self, rqueue, wqueue):
        super(Server, self).__init__()
        self.rq = rqueue
        self.wq = wqueue

        global RQ
        global WQ
        RQ = rqueue
        WQ = wqueue

    def run(self):
        app.run(use_reloader=False)


