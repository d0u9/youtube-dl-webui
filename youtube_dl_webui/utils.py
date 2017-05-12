#!/usr/bin/env python
# -*- coding: utf-8 -*-

class YoutubeDLWebUI(Exception):
    """Base exception for YoutubeDL errors."""
    pass


class TaskError(YoutubeDLWebUI):
    """Error related to download tasks."""
    def __init__(self, msg, tid=None, url=None, state=None):
        if tid:
            msg += ' tid={}'.format(tid)
        if url:
            msg += ' url={}'.format(url)
        if state:
            msg += ' state={}'.format(state)

        super(TaskError, self).__init__(msg)
        self.tid = tid
        self.url = url
        self.state = state
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

class YDLManagerError(YoutubeDLWebUI):
    """Error related to youtube-dl manager."""
    def __init__(self, msg, tid=None, url=None, state=None):
        if tid:
            msg += ' tid={}'.format(tid)
        if url:
            msg += ' url={}'.format(url)
        if state:
            msg += ' state={}'.format(state)

        super(YDLManagerError, self).__init__(msg)
        self.tid = tid
        self.url = url
        self.state = state
        self.msg = msg

    def __str__(self):
        return repr(self.msg)
