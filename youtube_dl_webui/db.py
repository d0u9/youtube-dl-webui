#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sqlite3

from hashlib import sha1
from time import time

from .utils import state_index, state_name
from .utils import TaskExistenceError
from .utils import TaskInexistenceError
from .utils import TaskPausedError
from .utils import TaskRunningError

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
                        (tid, url, time()))
        ydl_opt_str = json.dumps(ydl_opts)
        self.db.execute('INSERT INTO task_ydl_opt (tid, opt) VALUES (?, ?)', (tid, ydl_opt_str))
        self.conn.commit()

        return tid


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

        if row['state'] == state_index['paused']:
            raise TaskPausedError('')

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


    def start_task(self, tid, ignore_state=False):
        self.db.execute('SELECT * FROM task_status WHERE tid=(?)', (tid, ))
        row = self.db.fetchone()
        if row is None:
            raise TaskInexistenceError('')

        if row['state'] == state_index['downloading'] and ignore_state is False:
            raise TaskRunningError('')

        state = state_index['downloading']
        self.db.execute('UPDATE task_status SET state=?, start_time=? WHERE tid=(?)', (state, time(), tid))
        self.db.execute('UPDATE task_param SET state=? WHERE tid=(?)', (state, tid))
        self.db.execute('UPDATE task_info SET state=? WHERE tid=(?)', (state, tid))
        self.db.execute('UPDATE task_ydl_opt SET state=? WHERE tid=(?)', (state, tid))
        self.conn.commit()

        return json.loads(row['log'])


    def delete_task(self, tid):
        self.db.execute('DELETE FROM task_status WHERE tid=(?)', (tid, ))
        self.db.execute('DELETE FROM task_info WHERE tid=(?)', (tid, ))
        self.db.execute('DELETE FROM task_param WHERE tid=(?)', (tid, ))
        self.db.execute('DELETE FROM task_ydl_opt WHERE tid=(?)', (tid, ))
        self.conn.commit()


    def query_task(self, tid):
        self.db.execute('SELECT * FROM task_status, task_info WHERE task_status.tid=(?)', (tid, ))
        row = self.db.fetchone()
        if row is None:
            raise TaskInexistenceError('')

        ret = {}
        for key in row.keys():
            if key == 'state':
                ret[key] = state_name[row[key]]
            if key == 'log':
                ret['log'] = json.loads(row['log'])
            else:
                ret[key] = row[key]

        return ret

    def list_task(self):
        self.db.execute('SELECT * FROM task_status, task_info')
        rows = self.db.fetchall()

        ret = []
        state_counter = {'downloading': 0, 'paused': 0, 'finished': 0}
        if len(rows) == 0:
            return ret, state_counter

        keys = rows[0].keys()
        for row in rows:
            t = {}
            for key in keys:
                if key == 'state':
                    state = row[key]
                    t[key] = state_name[state]
                    state_counter[state_name[state]] += 1
                if key == 'log':
                    t['log'] = json.loads(row['log'])
                else:
                    t[key] = row[key]
            ret.append(t)

        print(ret)

        return ret, state_counter

    def list_state(self):
        state_counter = {'downloading': 0, 'paused': 0, 'finished': 0}

        self.db.execute('SELECT state, count(*) as NUM FROM task_status GROUP BY state')
        rows = self.db.fetchall()

        for r in rows:
            state_counter[state_name[r['state']]] = r['NUM']

        return state_counter

