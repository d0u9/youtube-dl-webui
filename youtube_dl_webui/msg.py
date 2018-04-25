#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from multiprocessing import Process, Queue

from .utils import new_uuid

class MsgBase(object):

    def __init__(self, getQ, putQ):
        self.getQ = getQ
        self.putQ = putQ


class SvrMsg(MsgBase):

    def __init__(self, getQ, putQ):
        super(SvrMsg, self).__init__(getQ, putQ)

    def put(self, data):
        payload = {'__data__': data}
        self.putQ.put(payload)


class CliMsg(MsgBase):

    def __init__(self, uuid, getQ, putQ):
        super(CliMsg, self).__init__(getQ, putQ)

        self.uuid = uuid

    def put(self, event, data):
        payload = {'__uuid__': self.uuid, '__event__': event, '__data__': data}
        self.putQ.put(payload)

    def get(self):
        raw_msg = self.getQ.get()
        return raw_msg['__data__']

class MsgMgr(object):
    _svrQ = Queue()
    _cli_dict = {}
    _evnt_cb_dict = {}

    def __init__(self):
        pass

    def new_cli(self, cli_name=None):
        uuid = None
        if cli_name is not None:
            # For named client, we create unique queue for communicating with server
            uuid = cli_name
            cli = CliMsg(cli_name, Queue(), self._svrQ)
        else:
            # Anonymous client is a client who needn't to talk to the server.
            uuid = new_uuid()
            cli = CliMsg(uuid, None, self._svrQ)

        self._cli_dict[uuid] = cli

        return cli

    def reg_event(self, event, cb_func, arg=None):
        # callback functions should have the signature of callback(svr, event, data, arg)
        #
        # svr is an instance of SrvMsg class, so the callback can directly send
        # mssages via svr to its corresponding client.
        self._evnt_cb_dict[event] = (cb_func, arg)

    def run(self):
        while True:
            raw_msg = self._svrQ.get()
            uuid = raw_msg['__uuid__']
            evnt = raw_msg['__event__']
            data = raw_msg['__data__']

            cli = self._cli_dict[uuid]
            cb  = self._evnt_cb_dict[evnt][0]
            arg = self._evnt_cb_dict[evnt][1]

            svr = SvrMsg(cli.putQ, cli.getQ)
            cb(svr, evnt, data, arg)

