#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask
from flask import render_template
from multiprocessing import Process

app = Flask(__name__)

Q = None

@app.route('/')
def index():
    Q.put('get index.html')
    return render_template('index.html')


class Server(Process):
    def __init__(self, queue):
        super(Server, self).__init__()
        self.q = queue

        global Q
        Q = queue

    def run(self):
        app.run()


