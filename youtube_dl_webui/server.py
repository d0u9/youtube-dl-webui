#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from flask import Flask
from flask import render_template
from flask import request
from multiprocessing import Process
from copy import deepcopy

MSG = None

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

    state = request.args.get('state', 'all')
    wqd['state'] = state

    WQ.put(wqd)
    return json.dumps(RQ.get())


@app.route('/task/state_counter', methods=['GET'])
def list_state():
    wqd = deepcopy(WQ_DICT)
    wqd['command'] = 'state'

    WQ.put(wqd)
    return json.dumps(RQ.get())


@app.route('/task/tid/<tid>', methods=['DELETE'])
def delete_task(tid):
    wqd = deepcopy(WQ_DICT)
    wqd['command'] = 'delete'
    wqd['tid'] = tid

    wqd['del_data'] = not not request.args.get('del_data', False)

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


@app.route('/config', methods=['GET', 'POST'])
def get_config():
    wqd = deepcopy(WQ_DICT)
    wqd['command'] = 'config'

    if request.method == 'POST':
        wqd['act'] = 'update'
        wqd['param'] = request.get_json()
    else:
        wqd['act'] = 'get'

    WQ.put(wqd)
    return json.dumps(RQ.get())


###
# test cases
###
@app.route('/test/<case>')
def test(case):
    return render_template('test/{}.html'.format(case))


class Server(Process):
    def __init__(self, rqueue, wqueue, host, port, m=None):
        super(Server, self).__init__()
        self.rq = rqueue
        self.wq = wqueue

        global RQ
        global WQ
        RQ = rqueue
        WQ = wqueue

        self.host = host
        self.port = port

        global MSG
        MSG = m

    def run(self):
        app.run(host=self.host, port=self.port, use_reloader=False)
        #  app.run(host='0.0.0.0', port=5000, use_reloader=False)


