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
import subprocess

from flask import Flask, url_for
from flask import request

import Context  #src\Context.py tell src location
import Request  #src\Request.py
import ConfigLoader  #src\ConfigLoader.py
import Output

app = Flask(__name__)

class HTTPRequestHandler(threading.Thread):
    def __init__(self, thread_id, thread_name, threads, event, send_report_event, request_queue, config, seperate):
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


    def thread_status(self):
        return self.status

    def handler(self, request, config, threads, seperate):
        global logger
        """
        if request["send_report"]:
            for thread in threads:
                while thread.thread_status() == 1:
                    # TODO:
                    time.sleep(self.config.timeout)
                    pass

            if seperate:
                # TODO: send multi-reports to admin
                pass
            else:
                print("A.mail");
                #os.system("./Mail.py --tag "+config.tag+" --offset 1 --threshold 1 --receiver "+request["mailto"]+" --subject \"報表\" --files \"output/APILog.csv\"")
            return
        """
        
        start_time = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d-%H:%M:%S")
        print("handler time:"+start_time) #網址可連的話才會Print
        logger.warn("handler time:"+start_time)
        
        if seperate: 
            _record = os.popen("./Main.py commandline --tag "+config.tag+" --url \""+request["url"]+"\" --title \""+request["title"]+"\" --context \""+request["context"]+"\"")
            record = _record.read().replace("\n", "")
            print("B record:"+record)
            #logger.warn(record)
        else:
            _record = os.popen("./Main.py commandline --tag "+config.tag+" --url \""+request["url"]+"\" --title \""+request["title"]+"\" --context \""+request["context"]+"\"" +" --timewarn \""+request["timewarn"]+"\"" +" --systep_id \""+request["systep_id"]+"\"")
            record = _record.read().replace("\n", "")
            #print("C record" + record)
            #logger.warn(record)

            print("C end")

        try:
            record = int(record)
            print("int record:" + record)
			
        except Exception as e:
            if config.debug_mode:
                print("config.debug_mode")
                print("APIServer: "+str(e)) 
            pass

        _record.close()
		
    def run(self):
        print("run")
        while not self.event.is_set():
            request = self.request_queue.get()
            if request is None:
                break
            #這段再看看是甚麼
            """
            if request["send_report"]: #if send_report = true
                self.send_report_event.set()
                self.status = 2

                self.handler(request, self.config, self.threads, self.seperate)

                self.status = 0
                self.send_report_event.clear()
            else:
                while self.send_report_event.is_set():
                    # TODO:
                    print("sleep?")
                    time.sleep(self.config.timeout)
                    pass
            
                self.status = 1
            """           
            self.handler(request, self.config, self.threads, self.seperate)

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
def arg_initialize(argv): #命令列說明
    parser = argparse.ArgumentParser(description="Start to running API server.")
    parser.add_argument("--threads", type=int, default=1, help="Specify number of worker threads. Default is 1.")
    parser.add_argument("--tag", help="Specify tag in the config.", default="APISERVER", required=True)
    parser.add_argument("--ip", help="Specify the binding address. Default is localhost.", default="localhost")
    parser.add_argument("--port", help="Specify the binding port. Default is 5000.", default=5000)
    seperate_group = parser.add_mutually_exclusive_group()
    seperate_group.add_argument("--onefile", default=False, dest="seperate", action="store_false", help="Default is onefile.")
    seperate_group.add_argument("--multifile", default=False, dest="seperate", action="store_true", help="Default is onefile.")
    #send_mail_group = parser.add_mutually_exclusive_group()
    #send_mail_group.add_argument("--sendmail", default=False, dest="send_mail", action="store_true", help="Default is not to send mail.")
    #send_mail_group.add_argument("--no-sendmail", default=False, dest="send_mail", action="store_false", help="Default is not to send mail.")

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

    #print("initialize")
    signal.signal(signal.SIGINT, signal_handler)
    logger = log_initialize("logs/apiserver.log")
    request_queue = queue.Queue()
    threads = []
    event = threading.Event()
    send_report_event = threading.Event()
    num_of_worker_threads = args.threads
    counter = 0
    conf = ConfigLoader.Config(filename="config/.requests.conf", tag=args.tag)
    conf.load_config()
    for i in range(0, num_of_worker_threads, 1):
        thread = HTTPRequestHandler(i, str(i), threads, event, send_report_event, request_queue, conf, args.seperate)
        thread.start()
        threads.append(thread)

@app.route("/")
def api_root():
    return "Welcome~<br><br>You are now in "+url_for("api_root")+".<br>The following APIs are offered for you.<br><br>/exec?title=&url=&context=&timewarn=&systep_id=<br>title, url, context, timewarn, systep_id are options."

@app.route("/exec")
def exec():
    global counter, logger, thread, request_queue
    #print("in")
    dt = datetime.datetime.strftime(datetime.datetime.now(), "%Y/%m/%d-%H:%M:%S")
    counter += 1
    if "title" in request.args and "url" in request.args:
        #如果有寫title和url 填進log
        logger.warn(str(counter)+" "+request.args["title"]+" "+request.args["url"]+" "+request.args["context"]+" "+request.args["timewarn"]+" "+request.args["systep_id"])
        pattern = "^http(s)?://"
        if not re.match(pattern, request.args["url"]): #網址要有http or https
            logger.warn(str(counter)+" "+request.args["title"]+": Syntax error on url argument.")
            #還是繼續做 把錯誤寫進DB
            #return "Syntax error on url argument." 

        #抓參數值
        title = request.args["title"]
        url = request.args["url"]
        context = request.args["context"]
        timewarn = request.args["timewarn"]
        systep_id = request.args["systep_id"]
        #auth = request.args["auth"]
        
        if(url==""):
            url="None"
        #request_queue is key,把資料丟到queue待處理,handler()
        request_queue.put({"counter": counter, "title": title, "url": url, "context": context, "timewarn": timewarn, "systep_id": systep_id, "datetime": dt})
        data = "[\"title\": "+request.args["title"]+", \"url\": "+request.args["url"]+", \"context\": "+request.args["context"]+"]"+", \"timewarn\": "+request.args["timewarn"]+"]"+", \"systep_id\": "+request.args["systep_id"]+"]"
        return "We are working on it.<br>The followings are your input data: "+data
    else:
        logger.warn(str(counter)+" Something wrong happend. Check you have send whole parameters.")
         #還是繼續做 把錯誤寫進DB
        #return "Something wrong happend. Make sure that you have already send the total five arguments."


if __name__ == "__main__":
    # TODO: Come in request log(who use it), output mail log(See PPT), 
    argv = sys.argv
    args = arg_initialize(argv)
    initialize(args)
    app.run(host=args.ip, port=args.port)
