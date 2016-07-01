#!/usr/local/bin/python3
# -*- coding:utf-8 -*-

from flask import Flask, url_for
from flask import request

app = Flask(__name__)

@app.route("/")
def api_root():
    return "Welcome~<br><br>You are now in "+url_for("api_root")+".<br>The following APIs are offered for you.<br><br>/exec/{title}/{url}/{admin}<br>/exec?title=&url=&admin="

@app.route("/exec/<title>/<url>/<admin>")
def api_execute(title, url, admin):
    return "We are working on it.<br>The followings are your input data: [\"title\": "+title+", \"url\": "+url+", \"admin\": "+admin+"]"

@app.route("/exec")
def api_execute_adv():
    if "title" in request.args and "url" in request.args and "admin" in request.args:
        return "We are working on it.<br>The followings are your input data: [\"title\": "+request.args["title"]+", \"url\": "+request.args["url"]+", \"admin\": "+request.args["admin"]+"]"

if __name__ == "__main__":
    app.run()
