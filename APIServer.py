#!/usr/local/bin/python3
# -*- coding:utf-8 -*-

from flask import Flask, url_for
from flask import request
import re
import os
import logging
import threading
import datetime
import queue
import signal
import sys
import argparse

app = Flask(__name__)

class HTTPRequestHandler(threading.Thread):
    def __init__(self, thread_id, thread_name, event, request_queue, seperate):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.thread_name = thread_name
        self.event = event
        self.request_queue = request_queue
        self.seperate = seperate

    def handler(self, request, seperate):
        global logger

        if seperate:
            record = os.popen("./Main.py commandline --tag WEBCHECK --no-verify-cert --redirect --no-auth --url "+request["url"]+" --title \""+request["title"]+"\" --email \""+request["mailto"]+"\" --unit \""+request["unit"]+"\" --filename \""+request["title"]+"\"").read().replace("\n", "")
        else:
            record = os.popen("./Main.py commandline --tag WEBCHECK --no-verify-cert --redirect --no-auth --url "+request["url"]+" --title \""+request["title"]+"\" --email \""+request["mailto"]+"\" --unit \""+request["unit"]+"\" --filename \"APILog\"").read().replace("\n", "")

        if record in ["400", "401", "403", "404", "500", "503", "-3", "-5"]:
            print(str(request["counter"])+" "+request["title"])
            print("Output. ("+record+")")
            error_msg = error_code_description(int(record))
            # temp
            print("./Mail.py --tag WEBCHECK --sender hyili@itri.org.tw --receiver a19931031@gmail.com --ccreceiver "+request["mailcc"]+" --subject \"您好，<br>請查收"+request["title"]+"網站無法提供正常服務之參考資訊，謝謝！\" --content \"<html><style>body {font-family:Microsoft JhengHei;}</style><body>ITRI對外資訊系統登錄及管理平台提供貼心網站偵測服務，每天早上定期為您負責的網站進行偵測，無法提供正常服務時會發信通知您。<br>目前已於 "+request["datetime"]+" 偵測到您所管理的「<a href="+request["url"]+">"+request["title"]+"</a>」<a href="+request["url"]+">"+request["url"]+"</a> 出現"+error_msg+"<br>提醒您所有報表皆透由機器自動做偵測和記錄，僅能呈現程式運作當下網站實際狀況，以上結果僅供參考。<br>任何問題，或有收通知信之困擾，歡迎聯絡 蘇益慧#17234 、張惠娟#13968，謝謝您～<br></body></html>\"")
            logger.warn(str(request["counter"])+" "+request["title"]+" "+request["url"]+" "+request["mailto"]+" "+request["mailcc"]+" "+request["unit"]+" sent OK")
        else:
            print(str(request["counter"])+" "+request["title"])
            print("No output. ("+record+")")
            logger.warn(str(request["counter"])+" "+request["title"]+" "+request["url"]+" "+request["mailto"]+" "+request["mailcc"]+" "+request["unit"]+" no sent OK")

    def run(self):
        while not self.event.is_set():
            request = self.request_queue.get()
            if request is None:
                break
            self.handler(request, self.seperate)

"""
Ctrl + C handler
"""
def signal_handler(signal, frame):
    global threads, event, num_of_worker_threads, request_queue

    for i in range(0, num_of_worker_threads, 1):
        request_queue.put(None)
    event.set()
    for thread in threads:
        thread.join()

    quit()

"""
Error code in Chinese
"""
def error_code_description(record):
    if (record == 400):
        return "http 錯誤 400 Bad Request   請求網址被伺服器判定格式錯誤<br>"
    elif (record == 401):
        return "http 錯誤 401 Unauthorized  沒有授權<br>"
    elif (record == 403):
        return "http 錯誤 403 Forbidden 禁止存取<br>"
    elif (record == 404):
        return "http 錯誤 404 Not Found 找不到檔案或目錄，可能原因為：<br>．檔案網頁不存在或已移除<br>．檔案網頁已被重新命名<br>．檔案網頁已經刪除或移至其他位置<br>．網址連結錯誤<br>...<br>"
    elif (record == 500):
        return "http 錯誤 500 Internal Server Error內部伺服器錯誤，可能原因為：<br>．無法存取要求的網頁，因為與該網頁相關的設定資料不正確<br>．伺服器當機<br>．網頁程式錯誤<br>．資料庫連結錯誤<br>...<br>"
    elif (record == 503):
        return "http 錯誤 503 Service Unavailable 服務無法使用<br>"
    elif (record == -3):
        return "http 錯誤 -3 超時：超過程式偵測所設定的 20秒而尚未回應網頁，提醒您：請檢查貴網站的呈現效能，並盡可能進行網站優化<br>"
    elif (record == -5):
        return "http 錯誤 -5 偵測無法成功建立連結並回傳http狀態值，可能原因為：<br>．DNS查詢失敗，節點/伺服器名稱無法提供或未知 Nodename nor servname provided, or not known<br>．網路無法使用Network is unreachable<br>．無法路由至主機，傳送端和接收端之間存在網路問題 No route to host<br>．目標主機主動拒絕，連結不能建立 Connection refused<br>...<br>"
    return ""

"""
Argument init
"""
def arg_initialize(argv):
    parser = argparse.ArgumentParser(description="Start to running API server.")
    parser.add_argument("--threads", type=int, default=1, help="Specify number of worker threads. Default is 1.")
    seperate_group = parser.add_mutually_exclusive_group(required=True)
    seperate_group.add_argument("--onefile", dest="seperate", action="store_false", help="Default is false.")
    seperate_group.add_argument("--multifile", dest="seperate", action="store_true", help="Default is true.")

    return parser.parse_args()

"""
Logger init
"""
def log_initialize(logname):
    directory = "logs/"
    logger = logging.getLogger("apiserver")
    logger.setLevel(logging.WARNING)
    file_handler = logging.FileHandler(directory+logname)
    file_handler.setLevel(logging.WARNING)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

"""
Initialize variable
"""
def initialize(args):
    global logger, request_queue, threads, event, num_of_worker_threads, counter

    signal.signal(signal.SIGINT, signal_handler)
    logger = log_initialize("apiserver.log")
    request_queue = queue.Queue()
    threads = []
    event = threading.Event()
    num_of_worker_threads = args.threads
    counter = 0
    for i in range(0, num_of_worker_threads, 1):
        thread = HTTPRequestHandler(i, str(i), event, request_queue, args.seperate)
        thread.start()
        threads.append(thread)

@app.route("/")
def api_root():
    return "Welcome~<br><br>You are now in "+url_for("api_root")+".<br>The following APIs are offered for you.<br><br>/exec?title=&url=&mailto=&mailcc=&unit="

@app.route("/exec")
def api_execute_adv():
    global counter, logger, thread, request_queue

    dt = datetime.datetime.strftime(datetime.datetime.now(), "%Y/%m/%d-%H:%M:%S")
    counter += 1
    if "title" in request.args and "url" in request.args and "mailto" in request.args and "mailcc" in request.args and "unit" in request.args:
        logger.warn(str(counter)+" "+request.args["title"]+" "+request.args["url"]+" "+request.args["mailto"]+" "+request.args["mailcc"]+" "+request.args["unit"])
        pattern = "^http(s)?://"
        if not re.match(pattern, request.args["url"]):
            logger.warn(str(counter)+" "+request.args["title"]+": Syntax error on url argument.")
            return "Syntax error on url argument."
        pattern = "^(((.*?)@(.*?));)+$"
        if not re.match(pattern, request.args["mailto"]):
            logger.warn(str(counter)+" "+request.args["title"]+": Syntax error on mailto argument.")
            return "Syntax error on mailto argument."
        pattern = "^(((.*?)@(.*?));)*$"
        if not re.match(pattern, request.args["mailcc"]):
            logger.warn(str(counter)+" "+request.args["title"]+": Syntax error on mailcc argument.")
            return "Syntax error on mailcc argument."

        title = request.args["title"]
        url = request.args["url"]
        mailto = request.args["mailto"].replace(";", " ")
        mailcc = request.args["mailcc"].replace(";", " ")
        unit = request.args["unit"]

        request_queue.put({"counter": counter, "title": title, "url": url, "mailto": mailto, "mailcc": mailcc, "unit": unit, "datetime": dt})

        data = "[\"title\": "+request.args["title"]+", \"url\": "+request.args["url"]+", \"mailto\": "+request.args["mailto"]+", \"mailcc\": "+request.args["mailcc"]+", \"unit\": "+request.args["unit"]+"]"
        return "We are working on it.<br>The followings are your input data: "+data
    else:
        logger.warn(str(counter)+" Something wrong happend. Check you have send whole parameters.")
        return "Something wrong happend. Make sure that you have already send the total five arguments."

if __name__ == "__main__":
    argv = sys.argv

    args = arg_initialize(argv)
    initialize(args)
    app.run()
