#!/usr/bin/env python
# -*- coding: utf-8 -*-

class TaskQueue(object):
    def __init__(self):
        self.queue = []


class TaskDesc(object):
    def __init__(self):
        self.info = {
                        'tid': self.tid,
                     'title': '',
                       'url': url,
                  'filename': '',
               'create_time': time(),
               'finish_time': time(),
                    'format': 0
                    }

        self.status = {
                        'tid': self.tid,
                   'percent': '0.0',
                  'filename': '',
               'tmpfilename': '',
          'downloaded_bytes': 0,
               'total_bytes': 0,
      'total_bytes_estimate': 0,
                     'speed': 0,
                       'eta': 0,
                   'elapsed': 0,
                'start_time': time(),
                'pause_time': time(),
                     'state': task_desc.state_index['paused'],
                      'log' : deque(maxlen=opts['log_size'])
                    }


