#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import json

from copy import deepcopy
from os.path import expanduser

class conf_base(object):
    def __init__(self, valid_fields, conf_dict):
        # each item in the _valid_fields is a tuple represents
        # (key, default_val, type, validate_regex, call_function)
        self._valid_fields = valid_fields
        self._conf = {}
        self.load(conf_dict)

    def load(self, conf_dict):
        for field in self._valid_fields:
            key      = field[0]
            dft_val  = field[1]
            val_type = field[2]
            vld_regx = field[3]
            func     = field[4]

            # More check can be made here
            if key in conf_dict:
                self._conf[key] = conf_dict[key] if func is None else func(conf_dict.get(key, dft_val))
            elif dft_val is not None:
                self._conf[key] = dft_val if func is None else func(conf_dict.get(key, dft_val))


    def get_val(self, key):
        return self._conf[key]

    def __getitem__(self, key):
        return self.get_val(key)

    def set_val(self, key, val):
        self._conf[key] = val

    def __setitem__(self, key, val):
        self.set_val(key, val)

    def dict(self):
        return self._conf


class ydl_conf(conf_base):
    _valid_fields = [
            #(key,              default_val,                type,       validate_regex,     call_function)
            ('proxy',           None,                       'string',   None,               None),
            ('format',          None,                       'string',   None,               None),
        ]

    _task_settable_fields = set(['format'])

    def __init__(self, conf_dict={}):
        self.logger = logging.getLogger('ydl_webui')

        super(ydl_conf, self).__init__(self._valid_fields, conf_dict)

    def merge_conf(self, task_conf_dict={}):
        ret = deepcopy(self.dict())
        for key, val in task_conf_dict.items():
            if key not in self._task_settable_fields or val == '':
                continue
            ret[key] = val

        return ret


class svr_conf(conf_base):
    _valid_fields = [
            #(key,              default_val,                type,       validate_regex,     call_function)
            ('host',            '127.0.0.1',                'string',   None,               None),
            ('port',            '5000',                     'string',   None,               None),
        ]

    def __init__(self, conf_dict={}):
        self.logger = logging.getLogger('ydl_webui')

        super(svr_conf, self).__init__(self._valid_fields, conf_dict)


class gen_conf(conf_base):
    _valid_fields = [
            #(key,              default_val,                type,       validate_regex,     call_function)
            ('download_dir',    '~/Downloads/youtube-dl',   'string',   '',                 expanduser),
            ('db_path',         '~/.conf/ydl_webui.db',     'string',   '',                 expanduser),
            ('log_size',        10,                         'int',      '',                 None),
        ]

    def __init__(self, conf_dict={}):
        self.logger = logging.getLogger('ydl_webui')

        super(gen_conf, self).__init__(self._valid_fields, conf_dict)


class conf(object):
    _valid_fields = set(('youtube_dl', 'server', 'general'))

    ydl_conf = None
    svr_conf = None
    gen_conf = None

    def __init__(self, conf_file, conf_dict={}, cmd_args={}):
        self.logger = logging.getLogger('ydl_webui')
        self.conf_file = conf_file
        self.cmd_args = cmd_args
        self.load(conf_dict)

    def cmd_args_override(self):
        _cat_dict = {'host': 'server',
                     'port': 'server'}

        for key, val in self.cmd_args.items():
            if key not in _cat_dict or val is None:
                continue
            sub_conf = self.get_val(_cat_dict[key])
            sub_conf.set_val(key, val)

    def load(self, conf_dict):
        if not isinstance(conf_dict, dict):
            self.logger.error("input parameter(conf_dict) is not an instance of dict")
            return

        for f in self._valid_fields:
            if f == 'youtube_dl':
                self.ydl_conf = ydl_conf(conf_dict.get(f, {}))
            elif f == 'server':
                self.svr_conf = svr_conf(conf_dict.get(f, {}))
            elif f == 'general':
                self.gen_conf = gen_conf(conf_dict.get(f, {}))

        # override configurations by cmdline arguments
        self.cmd_args_override()

    def save2file(self):
        if self.conf_file is not None:
            try:
                with open(self.conf_file, 'w') as f:
                    json.dump(self.dict(), f, indent=4)
            except PermissionError:
                return (False, 'permission error')
            except FileNotFoundError:
                return (False, 'can not find file')
            else:
                return (True, None)

    def dict(self):
        d = {}
        for f in self._valid_fields:
            if f == 'youtube_dl':
                d[f] = self.ydl_conf.dict()
            elif f == 'server':
                d[f] = self.svr_conf.dict()
            elif f == 'general':
                d[f] = self.gen_conf.dict()

        return d

    def get_val(self, key):
        if key not in self._valid_fields:
            raise KeyError(key)

        if key == 'youtube_dl':
            return self.ydl_conf
        elif key == 'server':
            return self.svr_conf
        elif key == 'general':
            return self.gen_conf
        else:
            raise KeyError(key)

    def __getitem__(self, key):
        return self.get_val(key)

