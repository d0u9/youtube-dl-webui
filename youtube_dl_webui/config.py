#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json, os
from sqlite3 import dbapi2 as sqlite3


class ydl_opts(object):
    def __init__(self, conf):
        self.valid_options = set(['proxy'])
        self.conf = {}

        for key, val in conf.items():
            if key in self.valid_options:
                self.conf[key] = val;

    def dict(self):
        return self.conf


class public_config(object):
    def __init__(self, conf_dict):
        general_conf = conf_dict.get('general')
        self.download_dir = general_conf.get('download_dir', None)
        self.db_path = general_conf.get('db_path', None)
        self.db = None


class server_config(object):
    def __init__(self, conf_dict):
        server = conf_dict.get('server')
        self.host = server.get('host', '0.0.0.0')
        self.port = server.get('port', 5000)
        self.public = None


    def add_public_config(self, public_conf):
        self.public = public_conf


class manager_config(object):
    def __init__(self, conf_dict):
        self.dl_log_size = conf_dict.get('download_log_size', 10)
        self.public = None
        self.ydl_opts = None


    def add_public_config(self, public_conf):
        self.public = public_conf


    def add_ydl_opts(self, ydl_opts):
        self.ydl_opts = ydl_opts


class config(object):
    def __init__(self, cmd_args, conf_file=None):
        self.cmd_args = cmd_args

        if conf_file is not None:
            self.conf_file = conf_file
        else:
            self.conf_file = cmd_args.config

        with open(self.conf_file) as f:
            conf_dict = json.load(f)

        # load options from command line
        self._load_cmd_args_()

        self.public = public_config(conf_dict)
        self.server = server_config(conf_dict)
        self.server.add_public_config(self.public)
        self.manager = manager_config(conf_dict)
        self.manager.add_public_config(self.public)

        self.ydl_opts = ydl_opts(conf_dict.get('youtube_dl'))
        self.manager.add_ydl_opts(self.ydl_opts)

        self.prepare()


    def _load_cmd_args_(self):
        if self.cmd_args.host is not None:
            conf_dict['server']['host'] = self.cmd_args.host

        if self.cmd_args.port is not None:
            conf_dict['server']['port'] = self.cmd_args.host


    def prepare(self):
        self.create_dl_dir()
        self.connect_db()


    def create_dl_dir(self):
        dl_dir = self.public.download_dir
        if os.path.exists(dl_dir) and not os.path.isdir(dl_dir):
            print('[ERROR] The {} exists, but not a valid directory'.format(dl_dir))
            raise Exception('The download directory is not valid')


        if os.path.exists(dl_dir) and not os.access(dl_dir, os.W_OK | os.X_OK):
            print('[ERROR] The download directory: {} is not writable'.format(dl_dir))
            raise Exception('The download directory is not writable')

        if not os.path.exists(dl_dir):
            os.makedirs(dl_dir)


    def connect_db(self):
        db_path = self.public.db_path
        if os.path.exists(db_path) and not os.path.isfile(db_path):
            print('[ERROR] The db_path: {} is not a regular file'.format(db_path))
            raise Exception('The db_path is not valid')

        if os.path.exists(db_path) and not os.access(db_path, os.W_OK):
            print('[ERROR] The db_path: {} is not writable'.format(db_path))
            raise Exception('The db_path is not valid')

        # first time to create db
        if not os.path.exists(db_path):
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row
            with open('./schema.sql', mode='r') as f:
                db.cursor().executescript(f.read())
        else:
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row

        self.public.db = db



