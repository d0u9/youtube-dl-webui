#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

class server_config():
    def __init__(self, conf):
        self.host = conf.get('host', '0.0.0.0')
        self.port = conf.get('port', 5000)


class youtube_dl_conf():
    def __init__(self, conf):
        self.valid_options = set(['proxy'])
        self.conf = {}

        for key, val in conf.items():
            if key in self.valid_options:
                self.conf[key] = val;

    def dict(self):
        return self.conf


class manger_config():
    def __init__(self, general_conf={}, ydl_opts={}):
        self.ydl_opts = youtube_dl_conf(ydl_opts)
        self.download_dir = general_conf.get('download_dir', '/tmp/ydl')
        self.log_size = general_conf.get('log_size', 10)


def override_conf_file(conf_dict, args):
    if args.host is not None:
        conf_dict['server']['host'] = args.host

    if args.port is not None:
        conf_dict['server']['port'] = args.port


class config():
    def __init__(self, args):
        self.conf_file = args.config

        with open(self.conf_file) as conf_file:
            self.conf_dict = json.load(conf_file)

        # override the config file options by command line options
        override_conf_file(self.conf_dict, args)

        # server configs
        self.server = server_config(self.conf_dict.get('server', {}))

        # download manager configs
        self.manager = manger_config(self.conf_dict.get('general', {}), self.conf_dict.get('youtube_dl', {}))

        print (self.conf_dict)





