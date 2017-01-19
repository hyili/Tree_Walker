#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-


import re
import os
import sys
import time
import queue
import signal
import logging
import argparse
import datetime
import threading

from flask import Flask, url_for
from flask import request

import context
from src import Request
from src import ConfigLoader

app = Flask(__name__)

class HTTPRequestHandler(threading.Thread):
    def __init__(self, thread_id, thread_name, threads, event, send_report_event, request_queue, config, seperate, send_mail):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.thread_name = thread_name
        self.threads = threads
        # 0: is idling, 1: is running, 2: is reporting
        self.status = 0
        self.event = event
        self.send_report_event = send_report_event
        self.request_queue = request_queue
        self.config = config
        self.seperate = seperate
        self.send_mail = send_mail

    def thread_status(self):
        return self.status

    def handler(self, request, config, threads, seperate, send_mail):
        global logger

        if request["send_report"]:
            for thread in threads:
                while thread.thread_status() == 1:
                    # TODO:
                    time.sleep(self.config.timeout)
                    pass

            if send_mail:
                os.system("./Mail.py --tag APISERVER --offset 1 --threshold 1 --receiver "+request["mailto"]+" --subject \"報表\" --files \"output/APILog.csv\"")
            else:
                print("./Mail.py --tag APISERVER --offset 1 --threshold 1 --receiver "+request["mailto"]+" --subject \"報表\" --files \"output/APILog.csv\"")

            return

        if seperate:
            _record = os.popen("./Main.py commandline --tag APISERVER --url "+request["url"]+" --depth "+request["level"]+" --title \""+request["title"]+"\" --email \""+request["mailto"]+"\" --unit \""+request["unit"]+"\" --filename \""+request["title"]+"\" --description \""+request["empno"]+"\"")
            record = _record.read().replace("\n", "")
        else:
            _record = os.popen("./Main.py commandline --tag APISERVER --url "+request["url"]+" --depth "+request["level"]+" --title \""+request["title"]+"\" --email \""+request["mailto"]+"\" --unit \""+request["unit"]+"\" --filename \"APILog\" --description \""+request["empno"]+"\"")
            record = _record.read().replace("\n", "")

        try:
            record = int(record)
        except Exception as e:
            # print(e)
            pass

        if request["level"] == 0:
            if record in config.broken_link:
                print(str(request["counter"])+" "+request["title"])
                print("Output. ("+str(record)+")")
                error_msg = error_code_description(record)
                if send_mail:
                    os.system("./Mail.py --tag APISERVER --receiver "+request["mailto"]+" --ccreceiver "+request["mailcc"]+" --subject \"您好，請查收"+request["title"]+"網站無法提供正常服務之參考資訊，謝謝！\" --content \"<html><style>body {font-family:Microsoft JhengHei;}</style><body>各位網站/系統負責人及單位管理代表您好：<br><br>「<a href=https://webcheck.itri.org.tw/index.aspx>ITRI對外資訊系統登錄及管理平台</a>」已於2016/8/15(一)起提供貼心的網站失連偵測服務(Broken Link Checker)，每天下午定期為登錄的網站進行偵測，當網站首頁出現無效連結時，會發信通知該網站/系統負責人及單位管理代表。<br>目前已於 "+request["datetime"]+" 偵測到您所管理的「<a href="+request["url"]+">"+request["title"]+"</a>」<a href="+request["url"]+">"+request["url"]+"</a> 出現"+error_msg+"<br>附加說明：<br>1.      所有回報皆透由測試系統自動偵測和記錄，僅能呈現每日測試當下網站實際狀況，供相關負責人參考。<br>2.      目前網站首頁回報的失聯狀況範圍包含：<br>   a. 請求網址被伺服器判定格式錯誤等(400,401, 403, 404)<br>    b. 內部伺服器錯誤等 (500, 503)<br>  c. 超過20秒未回應，或無法成功建立連結<br>   其他需再做專業評估的例外情況，不包含於定期偵測回報的範圍。<br><br>任何問題，或有收通知信之困擾，歡迎聯絡蘇益慧(#17234)、張惠娟經理(#13968)，謝謝您～<br><br>本郵件為系統自動發送，請勿直接回信！<br></body></html>\"")
                else:
                    print("./Mail.py --tag APISERVER --receiver "+request["mailto"]+" --ccreceiver "+request["mailcc"]+" --subject \"您好，請查收"+request["title"]+"網站無法提供正常服務之參考資訊，謝謝！\" --content \"<html><style>body {font-family:Microsoft JhengHei;}</style><body>各位網站/系統負責人及單位管理代表您好：<br><br>「<a href=https://webcheck.itri.org.tw/index.aspx>ITRI對外資訊系統登錄及管理平台</a>」已於2016/8/15(一)起提供貼心的網站失連偵測服務(Broken Link Checker)，每天下午定期為登錄的網站進行偵測，當網站首頁出現無效連結時，會發信通知該網站/系統負責人及單位管理代表。<br>目前已於 "+request["datetime"]+" 偵測到您所管理的「<a href="+request["url"]+">"+request["title"]+"</a>」<a href="+request["url"]+">"+request["url"]+"</a> 出現"+error_msg+"<br>附加說明：<br>1.      所有回報皆透由測試系統自動偵測和記錄，僅能呈現每日測試當下網站實際狀況，供相關負責人參考。<br>2.      目前網站首頁回報的失聯狀況範圍包含：<br>   a. 請求網址被伺服器判定格式錯誤等(400,401, 403, 404)<br>    b. 內部伺服器錯誤等 (500, 503)<br>  c. 超過20秒未回應，或無法成功建立連結<br>   其他需再做專業評估的例外情況，不包含於定期偵測回報的範圍。<br><br>任何問題，或有收通知信之困擾，歡迎聯絡蘇益慧(#17234)、張惠娟經理(#13968)，謝謝您～<br><br>本郵件為系統自動發送，請勿直接回信！<br></body></html>\"")
                logger.warn(str(request["counter"])+" "+request["title"]+" "+request["url"]+" "+request["level"]+" "+request["mailto"]+" "+request["mailcc"]+" "+request["unit"]+" "+request["empno"]+" sent OK")
            else:
                print(str(request["counter"])+" "+request["title"])
                print("No output. ("+str(record)+")")
                logger.warn(str(request["counter"])+" "+request["title"]+" "+request["url"]+" "+request["level"]+" "+request["mailto"]+" "+request["mailcc"]+" "+request["unit"]+" "+request["empno"]+" no sent OK")
        else:
            logger.warn(str(request["counter"])+" "+request["title"]+" "+request["url"]+" "+request["level"]+" "+request["mailto"]+" "+request["mailcc"]+" "+request["unit"]+" "+request["empno"]+" no sent OK")
            print(record)
            pass

        _record.close()

    def run(self):
        while not self.event.is_set():
            request = self.request_queue.get()
            if request is None:
                break

            if request["send_report"]:
                self.send_report_event.set()
                self.status = 2

                self.handler(request, self.config, self.threads, self.seperate, self.send_mail)

                self.status = 0
                self.send_report_event.clear()
            else:
                while self.send_report_event.is_set():
                    # TODO:
                    time.sleep(self.config.timeout)
                    pass

                self.status = 1

                self.handler(request, self.config, self.threads, self.seperate, self.send_mail)

                self.status = 0

"""
Ctrl + C handler
"""
def signal_handler(signal, frame):
    global threads, event, num_of_worker_threads, request_queue

    print("Got it!")
    for i in range(0, num_of_worker_threads, 1):
        request_queue.put(None)
    event.set()
    for thread in threads:
        thread.join()

    print("Ready to quit!")
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
    seperate_group = parser.add_mutually_exclusive_group()
    seperate_group.add_argument("--onefile", default=False, dest="seperate", action="store_false", help="Default is onefile.")
    seperate_group.add_argument("--multifile", default=False, dest="seperate", action="store_true", help="Default is onefile.")
    send_mail_group = parser.add_mutually_exclusive_group()
    send_mail_group.add_argument("--sendmail", default=False, dest="send_mail", action="store_true", help="Default is not to send mail.")
    send_mail_group.add_argument("--no-sendmail", default=False, dest="send_mail", action="store_false", help="Default is not to send mail.")

    return parser.parse_args()

"""
Logger init
"""
def log_initialize(logname):
    logger = logging.getLogger("apiserver")
    logger.setLevel(logging.WARNING)
    file_handler = logging.FileHandler(logname)
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
    send_report_event = threading.Event()
    num_of_worker_threads = args.threads
    counter = 0
    conf = ConfigLoader.Config(filename="../sample/config/.requests.conf", tag="APISERVER")
    conf.load_config()
    for i in range(0, num_of_worker_threads, 1):
        thread = HTTPRequestHandler(i, str(i), threads, event, send_report_event, request_queue, conf, args.seperate, args.send_mail)
        thread.start()
        threads.append(thread)

@app.route("/")
def api_root():
    return "Welcome~<br><br>You are now in "+url_for("api_root")+".<br>The following APIs are offered for you.<br><br>/exec?title=&url=&mailto=&mailcc=&unit=&level=&empno=<br>unit, mailto, mailcc, level, and empno are options."

@app.route("/exec")
def exec():
    global counter, logger, thread, request_queue

    dt = datetime.datetime.strftime(datetime.datetime.now(), "%Y/%m/%d-%H:%M:%S")
    counter += 1
    if "title" in request.args and "url" in request.args:
        logger.warn(str(counter)+" "+request.args["title"]+" "+request.args["url"])
        pattern = "^http(s)?://"
        if not re.match(pattern, request.args["url"]):
            logger.warn(str(counter)+" "+request.args["title"]+": Syntax error on url argument.")
            return "Syntax error on url argument."

        title = request.args["title"]
        url = request.args["url"]
        unit = ""
        mailto = ""
        mailcc = ""
        level = "0"
        empno = ""

        try:
            unit = request.args["unit"]
        except Exception as e:
            #print(e)
            pass

        try:
            pattern = "^(((.*?)@(.*?));)*$"
            if not re.match(pattern, request.args["mailto"]):
                logger.warn(str(counter)+" "+request.args["title"]+": Syntax error on mailto argument.")
                return "Syntax error on mailto argument."
            mailto = request.args["mailto"].replace(";", " ")
        except Exception as e:
            #print(e)
            pass

        try:
            pattern = "^(((.*?)@(.*?));)*$"
            if not re.match(pattern, request.args["mailcc"]):
                logger.warn(str(counter)+" "+request.args["title"]+": Syntax error on mailcc argument.")
                return "Syntax error on mailcc argument."
            mailcc = request.args["mailcc"].replace(";", " ")
        except Exception as e:
            #print(e)
            pass

        try:
            level = str(int(request.args["level"]))
        except Exception as e:
            #print(e)
            pass

        try:
            empno = request.args["empno"]
        except Exception as e:
            #print(e)
            pass

        request_queue.put({"counter": counter, "title": title, "url": url, "mailto": mailto, "mailcc": mailcc, "unit": unit, "level": level, "empno": empno, "datetime": dt, "send_report": False})

        data = "[\"title\": "+request.args["title"]+", \"url\": "+request.args["url"]+", \"mailto\": "+mailto+", \"mailcc\": "+mailcc+", \"unit\": "+unit+", \"level\": "+level+", \"empno\": "+empno+"]"
        return "We are working on it.<br>The followings are your input data: "+data
    else:
        logger.warn(str(counter)+" Something wrong happend. Check you have send whole parameters.")
        return "Something wrong happend. Make sure that you have already send the total five arguments."

@app.route("/send_report")
def send_report():
    global request_queue, logger

    if "title" in request.args and "mailto" in request.args:
        logger.warn("Sending Report "+request.args["title"]+" "+request.args["mailto"])
        pattern = "^(((.*?)@(.*?));)+$"
        if not re.match(pattern, request.args["mailto"]):
            logger.warn("Sending Report "+request.args["title"]+": Syntax error on mailto argument.")
            return "Syntax error on mailto argument."

        title = request.args["title"]
        mailto = request.args["mailto"].replace(";", " ")

        request_queue.put({"title": title, "mailto": mailto, "send_report": True})

    return "Put in process queue."


if __name__ == "__main__":
    # TODO: Come in request log(who use it), output mail log(See PPT), 
    argv = sys.argv

    args = arg_initialize(argv)
    initialize(args)
    app.run(host="0.0.0.0")
