#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from os import chdir
import youtube_dl


class MyLogger(object):
    def debug(self, msg):
        print('dbg: ', msg)

    def warning(self, msg):
        print('warn: ', msg)

    def error(self, msg):
        print('err: ', msg)


def my_hook(d):
    print(d)
    if d['status'] == 'finished':
        print('--------------- finish -----------------')

if __name__ == '__main__':
    chdir('/tmp')

    ydl_opts = {
        'format': 'bestvideo+bestaudio',
        'logger': MyLogger(),
        'progress_hooks': [my_hook],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ret = ydl.extract_info('https://www.youtube.com/watch?v=jZvC7NWkeA0')
