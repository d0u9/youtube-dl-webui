#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sqlite3
import logging

from hashlib import sha1
from time import time

from .utils import state_index, state_name
from .utils import TaskExistenceError
from .utils import TaskInexistenceError
from .utils  import url2tid

class DataBase(object):
    def __init__(self, db_path):
        self.logger = logging.getLogger('ydl_webui')
        if os.path.exists(db_path) and not os.path.isfile(db_path):
            self.logger.error('The db_path: %s is not a regular file', db_path)
            raise Exception('The db_path is not valid')

        if os.path.exists(db_path) and not os.access(db_path, os.W_OK):
            self.logger.error('The db_path: %s is not writable', db_path)
            raise Exception('The db_path is not valid')

        # first time to create db
        if not os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            #  conn = sqlite3.connect(":memory:")
            conn.row_factory = sqlite3.Row
            db = conn.cursor()
            db_path = os.path.dirname(os.path.abspath(__file__))
            db_file = db_path + '/schema.sql'
            with open(db_file, mode='r') as f:
                conn.executescript(f.read())
        else:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            db = conn.cursor()

        self.db = db
        self.conn = conn

        # Get tables
        self.tables = {}
        self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for row in self.db.fetchall():
            self.tables[row['name']] = None

        for table in self.tables:
            c = self.conn.execute('SELECT * FROM {}'.format(table))
            self.tables[table] = [desc[0] for desc in c.description]

    def update(self, tid, val_dict={}):
        for table, data in val_dict.items():
            if table not in self.tables:
                self.logger.warning('table(%s) does not exist' %(table))
                continue

            f, v = '', []
            for name, val in data.items():
                if name in self.tables[table]:
                    if val is not None:
                        f = f + '{}=(?),'.format(name)
                        v.append(val)
                else:
                    self.logger.warning('field_name(%s) does not exist' %(name))
            else:
                f = f[:-1]

            v.append(tid)
            self.db.execute('UPDATE {} SET {} WHERE tid=(?)'.format(table, f), tuple(v))

        self.conn.commit()

    def get_ydl_opts(self, tid):
        self.db.execute('SELECT opt FROM task_ydl_opt WHERE tid=(?)', (tid, ))
        row = self.db.fetchone()

        if row is None:
            raise TaskInexistenceError('task does not exist')

        return json.loads(row['opt'])

    def get_stat(self, tid):
        self.db.execute('SELECT * FROM task_status WHERE tid=(?)', (tid, ))
        row = self.db.fetchone()

        if row is None:
            raise TaskInexistenceError('task does not exist')

        return dict(row)

    def get_info(self, tid):
        self.db.execute('SELECT * FROM task_info WHERE tid=(?)', (tid, ))
        row = self.db.fetchone()

        if row is None:
            raise TaskInexistenceError('task does not exist')

        return dict(row)

    def new_task(self, url, ydl_opts):
        tid = url2tid(url)

        self.db.execute('SELECT * FROM task_status WHERE tid=(?)', (tid, ))
        if self.db.fetchone() is not None:
            raise TaskExistenceError('Task exists')

        ydl_opts_str = json.dumps(ydl_opts)

        self.db.execute('INSERT INTO task_status (tid, url) VALUES (?, ?)', (tid, url))
        self.db.execute('INSERT INTO task_info (tid, url, create_time) VALUES (?, ?, ?)',
                        (tid, url, time()))
        self.db.execute('INSERT INTO task_ydl_opt (tid, url, opt) VALUES (?, ?, ?)',
                        (tid, url, ydl_opts_str))
        self.conn.commit()

        return tid

    def start_task(self, tid, start_time=time()):
        state = state_index['downloading']
        db_data =   {
                        'task_info': {'state': state},
                        'task_status': {'start_time': start_time, 'state': state},
                        'task_ydl_opt': {'state': state},
                    }
        self.update(tid, db_data)

    def pause_task(self, tid, elapsed, pause_time=time()):
        self.logger.debug("db pause_task()")
        state = state_index['paused']
        db_data =   {
                        'task_info': {'state': state},
                        'task_status': {'pause_time': pause_time,
                                        'eta': 0,
                                        'speed': 0,
                                        'elapsed': elapsed,
                                        'state': state,
                        },
                        'task_ydl_opt': {'state': state},
                    }
        self.update(tid, db_data)

    def finish_task(self, tid, elapsed, finish_time=time()):
        self.logger.debug("db finish_task()")
        state = state_index['finished']
        db_data =   {
                        'task_info': {  'state': state,
                                        'finish_time': finish_time,
                        },
                        'task_status': {'pause_time': finish_time,
                                        'eta': 0,
                                        'speed': 0,
                                        'elapsed': elapsed,
                                        'state': state,
                                        'percent': '100.0%',
                        },
                        'task_ydl_opt': {'state': state},
                    }
        self.update(tid, db_data)

    def halt_task(self, tid, elapsed, halt_time=time()):
        self.logger.debug('db halt_task()')
        state = state_index['invalid']
        db_data =   {
                        'task_info': {  'state': state,
                                        'finish_time': halt_time,
                        },
                        'task_status': {'pause_time': halt_time,
                                        'eta': 0,
                                        'speed': 0,
                                        'elapsed': elapsed,
                                        'state': state,
                        },
                        'task_ydl_opt': {'state': state},
                    }
        self.update(tid, db_data)

    def delete_task(self, tid):
        """ return the tmp file or file downloaded """
        self.db.execute('SELECT * FROM task_status WHERE tid=(?)', (tid, ))
        row = self.db.fetchone()
        if row is None:
            raise TaskInexistenceError('')

        dl_file = row['filename']

        self.db.execute('DELETE FROM task_status WHERE tid=(?)', (tid, ))
        self.db.execute('DELETE FROM task_info WHERE tid=(?)', (tid, ))
        self.db.execute('DELETE FROM task_ydl_opt WHERE tid=(?)', (tid, ))
        self.conn.commit()

        return dl_file

    def query_task(self, tid):
        self.db.execute('SELECT * FROM task_status, task_info, task_ydl_opt WHERE task_status.tid=(?) and task_info.tid=(?) and task_ydl_opt.tid=(?)', (tid, tid, tid))
        row = self.db.fetchone()
        if row is None:
            raise TaskInexistenceError('')

        ret = {}
        for key in row.keys():
            if key == 'state':
                ret[key] = state_name[row[key]]
            elif key == 'log':
                ret['log'] = json.loads(row['log'])
            else:
                ret[key] = row[key]

        return ret

    def list_task(self, state):
        self.db.execute('SELECT * FROM task_status, task_info WHERE task_status.tid=task_info.tid')
        rows = self.db.fetchall()

        state_counter = {'downloading': 0, 'paused': 0, 'finished': 0, 'invalid': 0}
        ret_val = []
        for row in rows:
            t = {}
            for key in set(row.keys()):
                if key == 'state':
                    s = row[key]
                    t[key] = state_name[s]
                    state_counter[state_name[s]] += 1
                elif key == 'log':
                    t['log'] = json.loads(row[key])
                else:
                    t[key] = row[key]

            if state == 'all' or t['state'] == state:
                ret_val.append(t)

        return ret_val, state_counter

    def state_counter(self):
        state_counter = {'downloading': 0, 'paused': 0, 'finished': 0, 'invalid': 0}

        self.db.execute('SELECT state, count(*) as NUM FROM task_status GROUP BY state')
        rows = self.db.fetchall()

        for r in rows:
            state_counter[state_name[r['state']]] = r['NUM']

        return state_counter

    def update_info(self, tid, info_dict):
        self.logger.debug('db update_info()')
        db_data =   {
                        'valid':            1,      # info_dict is updated
                        'title':            info_dict['title'],
                        'format':           info_dict['format'],
                        'ext':              info_dict['ext'],
                        'thumbnail':        info_dict['thumbnail'],
                        'duration':         info_dict['duration'],
                        'view_count':       info_dict['view_count'],
                        'like_count':       info_dict['like_count'],
                        'dislike_count':    info_dict['dislike_count'],
                        'average_rating':   info_dict['average_rating'],
                        'description':      info_dict['description'],
                    }
        self.update(tid, {'task_info': db_data})

    def update_log(self, tid, log, exist_test=False):
        if exist_test:
            self.db.execute('SELECT * FROM task_status WHERE tid=(?)', (tid, ))
            row = self.db.fetchone()
            if row is None:
                raise TaskInexistenceError('')

        log_str = json.dumps([l for l in log])
        self.update(tid, {'task_status': {'log': log_str}})

    def progress_update(self, tid, d, elapsed):
        self.logger.debug("update filename=%s, tmpfilename=%s" %(d['filename'], d['tmpfilename']))

        db_data =   {
                        'percent':              d['_percent_str'],
                        'filename':             d['filename'],
                        'tmpfilename':          d['tmpfilename'],
                        'downloaded_bytes':     d['downloaded_bytes'],
                        'total_bytes':          d['total_bytes'],
                        'total_bytes_estmt':    d['total_bytes_estimate'],
                        'speed':                d['speed'],
                        'eta':                  d['eta'],
                        'elapsed':              elapsed,
                    }
        self.update(tid, {'task_status': db_data})

    def launch_unfinished(self):
        self.db.execute('SELECT tid FROM task_status WHERE state in (?)',
                        (state_index['downloading'],))

        rows = self.db.fetchall()

        ret_val = []
        for row in rows:
            ret_val.append(row['tid'])

        return ret_val


