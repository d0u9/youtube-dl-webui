#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route("/")
def hello():
    return render_template('index.html')

class server():
    def __init__(self):
        pass

    def run(self, conf):
        app.run(host=conf.host, port=conf.port)

