#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

class Core(object):
    def __init__(self, args=None):
        self.cmd_args = {}
        self.conf = {'server': {}, 'ydl': {}}

        if args is not None:
            self.load_cmd_args(args)

        self.load_conf_file()


    def load_cmd_args(self, args):
        self.cmd_args['conf'] = args.get('config', None)
        self.cmd_args['host'] = args.get('host', None)
        self.cmd_args['port'] = args.get('port', None)


    def load_conf_file(self):
        with open(self.cmd_args['conf']) as f:
            conf_dict = json.load(f)

        general = conf_dict.get('general', None)
        self.load_general_conf(general)

        server_conf = conf_dict.get('server', None)
        self.load_server_conf(server_conf)

        ydl_opts = conf_dict.get('youtube_dl', None)
        self.load_ydl_conf(ydl_opts)


    def load_general_conf(self, general):
        valid_conf = [  ('download_dir', '/tmp/'),
                        ('db_path', '/tmp/db.db'),
                        ('task_log_size', 10),
                     ]

        general = {} if general is None else general

        for pair in valid_conf:
            self.conf[pair[0]] = general.get(pair[0], pair[1])



    def load_server_conf(self, server_conf):
        valid_conf = [  ('host', '127.0.0.1'),
                        ('port', '5000')
                     ]

        server_conf = {} if server_conf is None else server_conf

        for pair in valid_conf:
            self.conf['server'][pair[0]] = server_conf.get(pair[0], pair[1])


    def load_ydl_conf(self, ydl_opts):
        valid_opts = ['proxy']

        ydl_opts = {} if ydl_opts is None else ydl_opts

        for opt in valid_opts:
            if opt in ydl_opts:
                self.conf['ydl'][opt] = ydl_opts.get(opt, None)
