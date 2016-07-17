#!/usr/local/bin/python3
# -*- coding:utf-8 -*-

from flask import Flask, url_for
from flask import request
import re
import os
import logging
import datetime

app = Flask(__name__)

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
        return "http 錯誤 -5 登錄網站連結失效，請檢查登錄網址是否正確以及伺服器是否正常運作<br>"
    return ""

"""
Logger init
"""
def log_initialize(logname):
    logger = logging.getLogger("requests")
    logger.setLevel(logging.WARNING)
    file_handler = logging.FileHandler(logname)
    file_handler.setLevel(logging.WARNING)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

logger = log_initialize(".APIServer.log")
counter = 0

@app.route("/")
def api_root():
    return "Welcome~<br><br>You are now in "+url_for("api_root")+".<br>The following APIs are offered for you.<br><br>/exec?title=&url=&mailto=&mailcc=&unit="

@app.route("/exec")
def api_execute_adv():
    global counter, logger

    pid = os.getpid()
    dt = datetime.datetime.strftime(datetime.datetime.now(), "%Y/%m/%d-%H:%M:%S")
    counter += 1
    if "title" in request.args and "url" in request.args and "mailto" in request.args and "mailcc" in request.args and "unit" in request.args:
        pattern = "^http(s)?://"
        if not re.match(pattern, request.args["url"]):
            logger.warn(request.args["title"]+": Syntax error on "+request.args["url"]+" argument.")
            return "Syntax error on url argument."
        pattern = "^(((.*?)@(.*?));)+$"
        if not re.match(pattern, request.args["mailto"]):
            logger.warn(request.args["title"]+": Syntax error on "+request.args["mailto"]+" argument.")
            return "Syntax error on mailto argument."
        pattern = "^(((.*?)@(.*?));)*$"
        if not re.match(pattern, request.args["mailcc"]):
            logger.warn(request.args["title"]+": Syntax error on "+request.args["mailcc"]+" argument.")
            return "Syntax error on mailcc argument."

        title = request.args["title"]
        url = request.args["url"]
        mailto = request.args["mailto"].replace(";", " ")
        mailcc = request.args["mailcc"].replace(";", " ")
        unit = request.args["unit"]

        os.fork()

        if pid != os.getpid():
            record = os.popen("./Main.py commandline --tag WEBCHECK --no-auth --url "+url+" --title \""+title+"\" --email \""+mailto+"\" --unit \""+unit+"\" --filename APILog").read().replace("\n", "")
            if record in ["400", "401", "403", "404", "500", "503", "-3", "-5"]:
                print(str(counter)+" "+title)
                print("Output. ("+record+")")
                error_msg = error_code_description(int(record))
                os.system("./Mail.py --tag WEBCHECK --sender hyili@itri.org.tw --receiver a19931031@gmail.com --secretccreceiver "+mailcc+" --subject \"請查收"+title+"網站無法提供正常服務之參考資訊，謝謝！\" --content \"<html><style>body {font-family:Microsoft JhengHei;}</style><body>ITRI對外資訊系統登錄及管理平台提供貼心網站偵測服務，每天早上定期為您負責的網站進行偵測，無法提供正常服務時會發信通知您。<br>目前已於 "+dt+" 偵測到您所管理的「<a href="+url+">"+title+"</a>網站」<a href="+url+">"+url+"</a> 出現"+error_msg+"<br>任何問題，或有收通知信之困擾，歡迎聯絡 蘇益慧#17234 、張惠娟#13968，謝謝您～<br></body></html>\"")
            else:
                print(str(counter)+" "+title)
                print("No output. ("+record+")")

            quit()

        data = "[\"title\": "+request.args["title"]+", \"url\": "+request.args["url"]+", \"mailto\": "+request.args["mailto"]+", \"mailcc\": "+request.args["mailcc"]+", \"unit\": "+request.args["unit"]+"]"
        return "We are working on it.<br>The followings are your input data: "+data

    return "Something wrong happend. Make sure that you have already send the total four arguments."

if __name__ == "__main__":
    app.run()