#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import datetime

from flask import Flask, url_for
from flask import request
from flask import render_template

app = Flask(__name__)

def initialize(_counter, _request_queue):
    global app
    global counter
    global request_queue

    counter = _counter
    request_queue = _request_queue

    return app

@app.route("/", methods=["Get"])
def api_root():
    return render_template("helloworld.html"), 200

@app.route("/exec", methods=["Get", "Post"])
def exec():
    global counter
    global request_queue

    # Get current time & update counter
    dt = datetime.datetime.strftime(datetime.datetime.now(), "%Y/%m/%d-%H:%M:%S")
    counter += 1

    # Handle get request
    if request.method == "Get":
        # Required parameter & Syntax check
        try:
            primid = request.args["id"]
        except Exception as e:
            return render_template("error_page.html", target="primid", exception=str(e)), 400

        try:
            subid = request.args["subid"]
        except Exception as e:
            subid = ""

        # Put the request into request_queue
        request_queue.put({
            "primid": primid,
            "subid": subid,
            "datetime": dt
        })

    # Handle post request
    elif request.method == "Post":
        # Required parameter & Syntax check
        try:
            primid = request.form["id"]
        except Exception as e:
            return render_template("error_page.html", target="primid", exception=str(e)), 400

        try:
            subid = request.form["subid"]
        except Exception as e:
            subid = ""

        # Put the request into request_queue
        request_queue.put({
            "primid": primid,
            "subid": subid,
            "datetime": dt
        })

    return render_template("pending_page.html",counter=counter), 200
