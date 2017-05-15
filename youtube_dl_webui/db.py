#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sqlite3

from hashlib import sha1
from time import time

from .utils import state_index
from .utils import TaskExistenceError
from .utils import TaskInexistenceError

class DataBase(object):
    def __init__(self, db_path):
        if os.path.exists(db_path) and not os.path.isfile(db_path):
            print('[ERROR] The db_path: {} is not a regular file'.format(db_path))
            raise Exception('The db_path is not valid')

        if os.path.exists(db_path) and not os.access(db_path, os.W_OK):
            print('[ERROR] The db_path: {} is not writable'.format(db_path))
            raise Exception('The db_path is not valid')

        # first time to create db
        if not os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            db = conn.cursor()
            with open('./schema.sql', mode='r') as f:
                conn.executescript(f.read())
        else:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            db = conn.cursor()

        self.db = db
        self.conn = conn


    def get_unfinished(self):
        self.db.execute('SELECT tid FROM task_status WHERE state!=?', (state_index['finished'], ))
        rows = self.db.fetchall()

        ret = []
        for row in rows:
            ret.append(row['tid'])

        return ret

    def get_param(self, tid):
        self.db.execute('SELECT * FROM task_param WHERE tid=(?) and state!=?', (tid, state_index['finished']))
        row = self.db.fetchone()

        if row is None:
            raise TaskInexistenceError('task does not exist')

        return {'tid', row['tid'], 'url', row['url']}


    def get_opts(self, tid):
        self.db.execute('SELECT opt FROM task_ydl_opt WHERE tid=(?) and state!=?', (tid, state_index['finished']))
        row = self.db.fetchone()

        if row is None:
            raise TaskInexistenceError('task does not exist')

        return json.loads(row['opt'])


    def get_ydl_opts(self, tid):
        self.db.execute('SELECT opt FROM task_ydl_opt WHERE tid=(?)', (tid, ))


    def create_task(self, param, ydl_opts):
        url = param['url']
        tid = sha1(url.encode()).hexdigest()

        self.db.execute('SELECT * FROM task_status WHERE tid=(?)', (tid, ))
        if self.db.fetchone() is not None:
            raise TaskExistenceError('Task exists')

        self.db.execute('INSERT INTO task_status (tid) VALUES (?)', (tid, ))
        self.db.execute('INSERT INTO task_param (tid, url) VALUES (?, ?)', (tid, url))
        self.db.execute('INSERT INTO task_info (tid, url, create_time) VALUES (?, ?, ?)',
                        (tid, time(), url))
        ydl_opt_str = json.dumps(ydl_opts)
        self.db.execute('INSERT INTO task_ydl_opt (tid, opt) VALUES (?, ?)', (tid, ydl_opt_str))
        self.conn.commit()


    def set_state(self, tid, state):
        if state not in state_index:
            raise KeyError

        self.db.execute('UPDATE task_status SET state=? WHERE tid=(?)', (state_index[state], tid))
        self.db.execute('UPDATE task_param SET state=? WHERE tid=(?)', (state_index[state], tid))
        self.db.execute('UPDATE task_info SET state=? WHERE tid=(?)', (state_index[state], tid))
        self.db.execute('UPDATE task_ydl_opt SET state=? WHERE tid=(?)', (state_index[state], tid))
        self.conn.commit()


    def pause_task(self,tid):
        self.db.execute('SELECT * FROM task_status WHERE tid=(?)', (tid, ))
        row = self.db.fetchone()
        if row is None:
            raise TaskInexistenceError('')

        cur_time = time()
        elapsed = row['elapsed']
        start_time = row['start_time']
        elapsed += (cur_time - start_time);

        state = state_index['paused']
        self.db.execute('UPDATE task_status SET state=?, pause_time=?, elapsed=? WHERE tid=(?)',
                        (state,  cur_time, elapsed, tid))
        self.db.execute('UPDATE task_param SET state=? WHERE tid=(?)', (state, tid))
        self.db.execute('UPDATE task_info SET state=? WHERE tid=(?)', (state, tid))
        self.db.execute('UPDATE task_ydl_opt SET state=? WHERE tid=(?)', (state, tid))
        self.conn.commit()


    def start_task(self, tid):
        state = state_index['downloading']
        self.db.execute('UPDATE task_status SET state=?, start_time=? WHERE tid=(?)', (state, time(), tid))
        self.db.execute('UPDATE task_param SET state=? WHERE tid=(?)', (state, tid))
        self.db.execute('UPDATE task_info SET state=? WHERE tid=(?)', (state, tid))
        self.db.execute('UPDATE task_ydl_opt SET state=? WHERE tid=(?)', (state, tid))
        self.conn.commit()


    def delete_task(self, tid):
        self.db.execute('DELETE FROM task_status WHERE tid=(?)', (tid, ))
        self.db.execute('DELETE FROM task_info WHERE tid=(?)', (tid, ))
        self.db.execute('DELETE FROM task_param WHERE tid=(?)', (tid, ))
        self.db.execute('DELETE FROM task_ydl_opt WHERE tid=(?)', (tid, ))
        self.conn.commit()

