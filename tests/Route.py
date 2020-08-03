#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import json
import datetime

from flask import Flask, url_for
from flask import request
from flask import render_template

app = Flask(__name__)

def initialize(_counter, _request_queue, _threads):
    global app
    global counter
    global request_queue
    global workers

    counter = _counter
    request_queue = _request_queue
    workers = _threads

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
    sample_usage = "curl -X POST http://localhost:5000/exec --data '{\"sid\": \"8401\", \"follow_redirection\": \"Y\", \"save_screenshot\": \"Y\", \"is_intra\": \"Y\"}' -H \"Content-Type: Application/json\""

    # Handle get request
    if request.method == "GET":
        return render_template("error_page.html", target="GET METHOD", exception="GET method not supported", usage=sample_usage), 400

    # Handle post request with json input
    elif request.method == "POST":
        data = request.get_json()
        data["datetime"] = dt
        data["counter"] = counter

        with open("logs/request", "ab") as f:
            print(str(dt)+" "+str(counter)+" "+str(data))
            f.write((str(dt)+" "+str(counter)+" "+str(data)+"\n").encode("utf-8-sig"))

        # Check if there has data
        if data is None:
            return render_template("error_page.html", target="POST METHOD", exception="POST with no JSON data.", usage=sample_usage), 400

        # Put the request into request_queue
        print("Waiting in queue.")
        request_queue.put(data)

    return render_template("pending_page.html", counter=counter, queue=request_queue.qsize()), 200

@app.route("/queue", methods=["Get"])
def queue():
    global counter
    global request_queue

    return render_template("queue_page.html", queue=request_queue.qsize()), 200

@app.route("/workers", methods=["Get"])
def workers():
    global workers

    workers_status = dict()
    for w in workers:
        workers_status[w.getName()] = {"Is_Alive": w.is_alive(), "Is_Idle": w.is_idle()}

    return render_template("workers_page.html", workers_status=workers_status), 200
