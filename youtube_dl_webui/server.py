#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from flask import Flask
from flask import render_template
from flask import request

app = Flask(__name__)

@app.errorhandler(500)
def S404(error):
    return '500 error'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/task', methods=['POST'])
def add_task():
    s = str(request.form)
    return s


class server():
    def __init__(self):
        pass

    def run(self, conf):
        app.run(host=conf.host, port=conf.port)

