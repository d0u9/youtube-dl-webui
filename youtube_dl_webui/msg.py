#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from multiprocessing import Process, Queue

from .utils import uuid

class Msg(object):
    _svrQ = Queue()

    def __init__(self, uuid, cliQ=False):
        self.uuid = uuid
        if cliQ is True:
            self._cliQ = Queue()
        else:
            self._cliQ = None

    def put(self, event, data):
        payload = {'__uuid__': self.uuid, '__event__': event, '__data__': data}
        Msg._svrQ.put(payload)

    def get(self):
        raw_msg = self._cliQ.get()
        uuid  = raw_msg['__uuid__']
        data  = raw_msg['__data__']

        return (uuid, data)

    def svr_put(self, data):
        payload = {'__uuid__': self.uuid, '__data__': data}
        self._cliQ.put(payload)

    @classmethod
    def svr_get(cls):
        raw_msg = cls._svrQ.get()
        print(raw_msg)
        uuid  = raw_msg['__uuid__']
        event = raw_msg['__event__']
        data  = raw_msg['__data__']

        return (uuid, event, data)


class MsgMgr(object):

    def __init__(self):
        self.logger = logging.getLogger('ydl_webui')
        self._cb_dict = {}
        self._msg_dict = {}

    def get_msg_handler(self, cli_name=None):
        if cli_name is not None:
            m = Msg(uuid=cli_name, cliQ=True)
            self._msg_dict[cli_name] = m
            return m
        else:
            uuid = uuid()
            m = Msg(uuid=uuid)
            self._msg_dict[uuid] = m
            return m

    def reg_event(self, event, callback):
        self._cb_dict[event] = callback

    def run(self):
        while True:
            uuid, event, data = Msg.svr_get()

            cb_func = self._cb_dict[event]
            cb_func(self._msg_dict[uuid], event, data)



