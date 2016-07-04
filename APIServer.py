#!/usr/local/bin/python3
# -*- coding:utf-8 -*-

from flask import Flask, url_for
from flask import request
import re
import os

app = Flask(__name__)

@app.route("/")
def api_root():
    return "Welcome~<br><br>You are now in "+url_for("api_root")+".<br>The following APIs are offered for you.<br><br>/exec/{title}/{url}/{mailto}<br>/exec?title=&url=&mailto="

@app.route("/exec/<title>/<url>/<mailto>/<mailcc>")
def api_execute(title, url, mailto, mailcc):
    data = "[\"title\": "+title+", \"url\": "+url+", \"mailto\": "+mailto+", \"mailcc\": "+mailcc+"]"
    return "We are working on it.<br>The followings are your input data: "+data

@app.route("/exec")
def api_execute_adv():
    pid = os.getpid()
    if "title" in request.args and "url" in request.args and "mailto" in request.args and "mailcc" in request.args:
        pattern = "^http(s)?://"
        if not re.match(pattern, request.args["url"]):
            return "Syntax error on url argument."
        pattern = "^(((.*?)@(.*?));)+$"
        if not re.match(pattern, request.args["mailto"]):
            return "Syntax error on mailto argument."
        pattern = "^(((.*?)@(.*?));)*$"
        if not re.match(pattern, request.args["mailcc"]):
            return "Syntax error on mailcc argument."

        title = request.args["title"]
        url = request.args["url"]
        mailto = request.args["mailto"].replace(";", " ")
        mailcc = request.args["mailcc"].replace(";", " ")

        os.fork()

        if pid != os.getpid():
            os.system("./Main.py commandline --tag COMMANDLINE --no-auth --url "+url+" --filename "+title+" > /dev/null 2>&1")
            os.system("./Mail.py --tag COMMANDLINE --sender suyihui.900360@itri.org.tw --receiver "+mailto+" --ccreceiver "+mailcc+" --secretccreceiver suyihui.900360@itri.org.tw --files "+title+".csv")
            quit()

        data = "[\"title\": "+request.args["title"]+", \"url\": "+request.args["url"]+", \"mailto\": "+request.args["mailto"]+", \"mailcc\": "+request.args["mailcc"]+"]"
        return "We are working on it.<br>The followings are your input data: "+data

    return "Something wrong happend. Make sure that you have already send the total four arguments."

if __name__ == "__main__":
    app.run()
