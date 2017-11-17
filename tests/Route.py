#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import json
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
    dt = datetime.datetime.now()
    counter += 1

    # Handle get request
    if request.method == "GET":
        # Required parameter & Syntax check
        try:
            primid = request.args["primid"]
        except Exception as e:
            return render_template("error_page.html", target="primid", exception="GET with no key primid"), 400

        try:
            subid = request.args["subid"]
        except Exception as e:
            subid = ""

        # TODO: TaskID?
        # Put the request into request_queue
        data = json.loads(json.dumps({
            "primid": primid,
            "subid": subid,
            "datetime": str(dt)
        }))
        print("Waiting in queue.")
        request_queue.put(data)

    # Handle post request with json input
    elif request.method == "POST":
        data = request.get_json()

        # Check if there has data
        if data is None:
            return render_template("error_page.html", target="primid", exception="POST with no JSON data."), 400

        # Required parameter & Syntax check
        if "primid" not in data:
            return render_template("error_page.html", target="primid", exception="POST with no key primid."), 400

        if "subid" not in data:
            data["subid"] = ""

        # TODO: TaskID?
        # Put the request into request_queue
        data["datetime"] = dt
        print("Waiting in queue.")
        request_queue.put(data)

    return render_template("pending_page.html", counter=counter), 200
