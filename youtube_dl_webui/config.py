#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from os.path import expanduser

class conf_base(object):
    _valid_fields = [
            # (key,              default_val,                type,       validate_regex,     call_function)
            ]

    _conf = {}

    def __init__(self, conf_json):
        self.load(conf_json)

    def load(self, conf_json):
        for field in self._valid_fields:
            key      = field[0]
            dft_val  = field[1]
            val_type = field[2]
            vld_regx = field[3]
            func     = field[4]

            # More check can be made here
            if key in conf_json:
                self._conf[key] = conf_json[key] if func is None else func(conf_json[key])
            elif dft_val is not None:
                self._conf[key] = dft_val if func is None else func(conf_json[key])

    def get_val(self, key):
        return self._conf[key]


class ydl_conf(conf_base):
    _valid_fields = [
            ('proxy',           None,                       'string',   None,               None),
            ('format',          None,                       'string',   None,               None),
        ]

    def __init__(self, conf_json={}):
        self.logger = logging.getLogger('ydl_webui')
        super(ydl_conf, self).__init__(conf_json)


class svr_conf(conf_base):
    _valid_fields = [
            ('host',            '127.0.0.1',                'string',   None,               None),
            ('port',            '5000',                     'string',   None,               None),
        ]

    def __init__(self, conf_json={}):
        self.logger = logging.getLogger('ydl_webui')
        super(ydl_conf, self).__init__(conf_json)


class gen_conf(conf_base):
    _valid_fields = [
            #(key,              default_val,                type,       validate_regex,     call_function)
            ('download_dir',    '~/Downloads/youtube-dl',   'string',   '',                 expanduser),
            ('db_path',         '~/.conf/ydl_webui.db',     'string',   '',                 expanduser),
            ('task_log_size',   10,                         'int',      '',                 None),
        ]

    def __init__(self, conf_json={}):
        self.logger = logging.getLogger('ydl_webui')
        super(ydl_conf, self).__init__(conf_json)


class conf(object):
    _valid_fields = set(('ydl', 'svr', 'gen'))

    ydl_conf = None
    svr_conf = None
    gen_conf = None

    def __init__(self, conf={}):
        self.logger = logging.getLogger('ydl_webui')
        self.load(conf)

    def load(self, conf):
        if not isinstance(conf, dict):
            self.logger.debug("input parameter(conf) is not an instance of dict")
            return
















