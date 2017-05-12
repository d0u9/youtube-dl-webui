#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json

from flask import Flask
from flask import render_template
from flask import request
from flask import g

from .manager import ydl_manger
from .utils import YDLManagerError

app = Flask(__name__)

def invalid_request():
    return json.dumps({'status': 'error', 'errmsg': 'invalid_request'})


def success():
    return json.dumps({'status': 'success'})


@app.errorhandler(404)
def not_found(error):
    return '404 not found'


@app.route('/')
def index():
    db = server.get_db()

    return render_template('index.html')


@app.route('/task', methods=['POST'])
def add_task():
    manager = server.get_manager()

    try:
        tid = manager.create_task({'url': request.form['url']})
        manager.start_task(tid)
    except YDLManagerError as e:
        return json.dumps({'status': 'error', 'errmsg': e.msg})

    return json.dumps({'status': 'success', 'tid': tid})


@app.route('/task/list', methods=['GET'])
def list_task():
    manager = server.get_manager()

    try:
        state = request.args.get('state', 'all')
        l = manager.list_tasks(state)
    except YDLManagerError as e:
        return json.dumps({'status': 'error', 'errmsg': e.msg})

    return json.dumps(l)


@app.route('/task/state_coutner', methods=['GET'])
def list_state():
    manager = server.get_manager()
    l = manager.state_list()
    return json.dumps(l)


@app.route('/task/tid/<tid>', methods=['DELETE'])
def delete_task(tid):
    manager = server.get_manager()
    act = request.args.get('del_data', None)

    try:
        if act == 'true':
            manager.delete_task(tid, True)
        else:
            manager.delete_task(tid)
    except YDLManagerError as e:
        return json.dumps({'status': 'error', 'errmsg': e.msg})

    return success()


@app.route('/task/tid/<tid>/status', methods=['GET'])
def query_task(tid):
    manager = server.get_manager()
    exerpt = request.args.get('exerpt', None)

    try:
        if exerpt == 'true':
            status = manager.query_task(tid, exerpt=True)
        else:
            status = manager.query_task(tid)
    except YDLManagerError as e:
        return json.dumps({'status': 'error', 'errmsg': e.msg})

    return json.dumps(status)


@app.route('/task/tid/<tid>', methods=['PUT'])
def manipulate_task(tid):
    manager = server.get_manager()

    act = request.args.get('act', None)
    if act is None:
        return invalid_request()

    try:
        if act == 'pause':
            manager.pause_task(tid)
        elif act == 'resume':
            manager.resume_task(tid)
        else:
            return json.dumps({'status': 'error', 'errmsg': 'unknow action'})
    except YDLManagerError as e:
        return json.dumps({'status': 'error', 'errmsg': e.msg})

    return success()


class server():
    manager = None
    db = None
    def __init__(self, conf):
        global app
        self.app = app
        self.conf = conf
        self.manager = None
        server.db = conf.public.db


    def run(self):
        self.app.run(host=self.conf.host, port=self.conf.port)


    def bind_ydl_manager(self, ydl_manager):
        self.manager = ydl_manager
        server.manager = ydl_manager

    @staticmethod
    def get_manager():
        manager = getattr(g, 'manager', None)

        if manager is None:
            manager = g.manager = server.manager

        return manager

    @staticmethod
    def get_db():
        db = getattr(g, 'db', None)

        if db is None:
            db = g.db = server.db

        return db

