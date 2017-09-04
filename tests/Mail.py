#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import os
import sys
import smtplib
import argparse
import datetime
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import Context
import ConfigLoader
import configparser

import pymssql  

"""
Argument init
"""
def arg_initialize(argv):
    parser = argparse.ArgumentParser(description="Start to send email.")
    parser.add_argument("--tag", help="Specify tag in the config.", required=True)
    parser.add_argument("--offset", type=int, help="Specify timing offset.")
    parser.add_argument("--threshold", type=int, help="Specify the threshold of sending the email.")
    parser.add_argument("--sender", default="", help="Specify sender email address.")
    parser.add_argument("--receiver", nargs="*", help="Specify receiver email addresses.", required=True)
    parser.add_argument("--ccreceiver", nargs="*", default=[], help="Specify ccreceiver email addresses. Default is nothing.")
    parser.add_argument("--secretccreceiver", nargs="*", default=[], help="Specify secret ccreceiver email addresses. Default is nothing.")
    parser.add_argument("--subject", default="", help="Specify the email subject.")
    parser.add_argument("--content", default="", help="Specify the email content.")
    #parser.add_argument("--files", nargs="*", default=[], help="Specify files that want to attach.")
    return parser.parse_args()

"""
Send the Email
"""
def send_mail(sender, receivers, ccreceivers, subject, content, username, password):
    msg = MIMEMultipart()
    msg["From"] = sender
    #msg["To"] = ", ".join(receivers)
    #msg["Cc"] = ", ".join(ccreceivers)
    msg["To"] = receivers
    msg["Cc"] = ccreceivers
    msg["Subject"] = subject
    _msg = MIMEText(content)
    _msg["Content-Type"] = "text/html"
    msg.attach(_msg)

    #"""
    try:
        smtp = smtplib.SMTP("smtpx.itri.org.tw")
        smtp.ehlo(name="itri.org.tw")
        smtp.login(user=username, password=password)
        smtp.sendmail(from_addr=sender, to_addrs=receivers+";"+ccreceivers, msg=msg.as_string())
        smtp.quit()
    except Exception as e:
        print("Mail: "+str(e))
        quit()
    #"""
"""
Prepare to send
"""
def main():
    argv = sys.argv
    args = arg_initialize(argv)

    #用來測試的
    tag = args.tag
    sender = args.sender
    receivers = args.receiver
    ccreceivers = args.ccreceiver
    #secretccreceivers = args.secretccreceiver
    subject = args.subject
    content = args.content

    #config
    config = ConfigLoader.Config(filename="config/.requests.conf", tag=tag)
    config.load_config()
    if sender == "":
        sender = config.user+"@itri.org.tw"
    username = config.user
    password = config.password

    #這裡Load mail資料進來
    DBconfig = configparser.ConfigParser()
    DBconfig.read('config/.config.conf')
    server = DBconfig.get('DB', 'SERVER').replace("\'","")
    DBusername = DBconfig.get('DB', 'USERNAME').replace("\'","")
    DBpassword = DBconfig.get('DB', 'PASSWORD').replace("\'","")
    database = DBconfig.get('DB', 'DATABASE').replace("\'","")

    conn = pymssql.connect(server=server, user=DBusername, password=DBpassword, database=database)
    cur = conn.cursor(as_dict=True)
    cur.execute("SELECT * FROM SYSINFO WHERE SENDSIGN = 1")
    results = cur.fetchall()
    print("here start db:")
    """
    L_ci_uid=[]
    L_sysname=[]
    L_sysurl=[]
    owner_mail=[]
    dire_usr_mail=[]
    """

    for S1 in results:
        content = createHeader()
        ci_uid = str(S1['CI_UID'])
        sysname = str(S1['SYSNAME'])
        sysurl = str(S1['SYSURL'])
        receivers = str(S1['OWNER_MAIL'])
        ccreceivers = str(S1['DIRE_USR_MAIL'])
        content += createTable(sysname,sysurl)
        subject = "[異常通知]「"+sysname+"」無法提供正常服務"
        """
        L_ci_uid.append(str(S1['CI_UID']))
        L_sysname.append(str(S1['SYSNAME']))
        L_sysurl.append(str(S1['SYSURL']))
        owner_mail.append(str(S1['OWNER_MAIL']))
        dire_usr_mail.append(str(S1['DIRE_USR_MAIL']))
        """

        #print("ci_uid:"+ci_uid+" ,sysname:"+str(sysname)+" ,sysurl:"+str(sysurl)+", owner_mail:"+str(owner_mail)+" ,dire_usr_mail:"+str(dire_usr_mail))
        #"""
        cur2 = conn.cursor()
        cur2.execute("SELECT ID,URL,TIMEWARN,CONTEXT,AUTH FROM SYSTEP WHERE CI_UID = '"+ci_uid+"' ORDER BY STEP")
        results2=cur2.fetchall()
        for S2 in results2:
            systep_id = str(S2[0])
            stepurl = str(S2[1])
            timewarn = str(S2[2])
            context = str(S2[3])
            auth = str(S2[4])
            #print("systep_id:"+str(systep_id)+" ,stepurl:"+str(stepurl)+" ,timewarn"+str(timewarn)+", context"+str(context)+" ,auth:"+str(auth))
            #"""
            cur3 = conn.cursor()
            cur3.execute("SELECT URL_STATUS,START_TIME,RESTIME,CONTEXT_STATUS FROM SYSTEP_RECORDS WHERE SYSTEP_ID = '"+str(systep_id)+"'")
            #the last one
            S3 = cur3.fetchone()
            url_status = str(S3[0])
            start_time = str(S3[1])
            restime = str(S3[2])
            context_status = str(S3[3])
            #print("url_status:"+url_status+" ,start_time:"+start_time+" ,restime:"+restime+" ,context_status:"+context_status)
            content += createSubTable(stepurl,timewarn,context,auth,url_status,start_time,restime,context_status)
            cur3.close()
            #"""
            #print("next run")
        content += "</td></tr></table>" #MainTableEnd
        cur2.close()
        #"""
        content += htmlEnd() #htmlEnd
        #測試先把content變空
        #content = ""
        if args.offset is not None and args.threshold is not None:
            offset = args.offset
            index = datetime.datetime.now()-datetime.timedelta(hours=offset)

            count = 0
            # TODO: log file format, and send mail problem
            log = os.popen("cat "+config.logpath+"/main.log")
            for line in log:
                part1 = line.split(" ")
                if part1[7] != "["+tag+"]":
                    continue
                part2 = part1[1].split(",")
                log_time = datetime.datetime.strptime(part1[0]+" "+part2[0], "%Y-%m-%d %H:%M:%S")
                if index <= log_time:
                    count += 1

            if count >= args.threshold:
                #send_mail(sender, receivers, ccreceivers, subject, content, username, password) #先把mail註解掉 上線再開
                print("Mail sent.(168)")
                print(content)
            else:
                print("Do nothing, --help for details.")
        else:
            #send_mail(sender, receivers, ccreceivers, subject, content, username, password)
            print("Mail sent.(174)")
            print(content)
        curU = conn.cursor()
        curU.execute("""UPDATE [SYSINFO] set [SENDSIGN] = 0 WHERE [CI_UID] = %s""",(ci_uid))
        conn.commit()

    cur.close()
    conn.close()

def htmlEnd():
    str = "<br/>附加說明：<br/>"
    str +="1.  所有回報皆透由測試系統自動偵測和記錄，僅能呈現每日測試當下網站實際狀況，供相關負責人參考。<br/>"
    str +="2.  目前網站首頁回報的失聯狀況範圍包含：<br/>"
    str += "&nbsp;&nbsp;a. 請求網址被伺服器判定格式錯誤等(400,401, 403, 404)<br/>"
    str += "&nbsp;&nbsp;b. 內部伺服器錯誤等 (500, 503)<br/>"
    str += "&nbsp;&nbsp;c. 超過20秒未回應，或無法成功建立連結<br/>"
    str += "其他需再做專業評估的例外情況，不包含於定期偵測回報的範圍。<br/>"
    str += "任何問題，或有收通知信之困擾，歡迎聯絡王貞凰(#17338)，謝謝您!<br/>"
    str += "(本郵件為檢測平台自動發送，請勿直接回信！)"
    str += "<br/><br/></body></html>"
    return str
	
def createTable(sysname,sysurl):
    
    table = "<table width='800' border='2' bordercolor='black'><tr><td width='150'>應用系統名稱：</td><td>" + sysname + "</td></tr>"
    table += "<tr><td>首頁網址：</td><td>" + sysurl + "</td></tr>"
    table += "<tr><td>執行網址與狀況：</td><td>"
    return table
    #print("sysname:"+str(sysname)+" ,sysurl:"+str(sysurl)+", owner_mail:"+str(owner_mail)+" ,dire_usr_mail:"+str(dire_usr_mail))

def createSubTable(stepurl,timewarn,context,auth,url_status,start_time,restime,context_status):
    table = "<table width='650' style='border-bottom:1px #0066FF solid;'><tr><td width='150'>執行網址：</td><td colspan=\"3\">" + stepurl + "</td></tr>"
    table += "<tr><td>是否需要SSO：</td>" 
    if(auth == "YES"):
        table += "<td colspan=\"3\">是</td></tr>"
    else:
        table += "<td colspan=\"3\">否</td></tr>"
    
    table += "<tr><td>檢查時間：</td><td colspan=\"3\">"+str(start_time)[0:-7]+"</td></tr>" 
    
    table += "<tr><td>執行狀態：</td>"
    if(url_status == "200"): 
        table += "<td colspan=\"3\">正常</td></tr>"
    else:
        #table += "<td colspan=\"3\"><font color=\"red\">"+url_status+"</font></td></tr>" #這裡改reason或用error code
        table += "<td colspan=\"3\"><font color=\"red\">"+error_code(url_status)+"</font></td></tr>"
        table += "<tr><td>錯誤原因可能為：</td><td colspan=\"3\">" + errorReason(url_status) + "</td></tr>"
    
    table += "<tr><td width='150'>回應時間門檻(秒)：</td><td width='175'>" + timewarn + "</td><td width='150'>花費時間(秒)：</td>"
    if(restime < timewarn): #正常
        table += "<td width='175'>"+restime+"</td>"
    else:
        table += "<td width='175'><font color=\"red\">" + restime
    
    if(url_status == "200"):
        table += "<tr><td width='150'>比對內容：</td><td width='175'>"+context+"</td><td width='150'>比對情況：</td>"
        if(context_status == "0"):
            table += "<td width='175'>正常</td></tr>"
        else:
            table += "<td width='175'><font color=\"red\">異常</td></tr>"
    #SubTable End
    table += "</table>"
    
    return table

def createHeader():
    header = "<html><style>body {font-family:Microsoft JhengHei;}</style>"
    header +="<body>各位網站/系統負責人您好：<br/>"
    header +="「Web-based資訊系統之服務檢測平台」每日定期為登錄的網站進行偵測，您所負責之網站/系統出現無效連結或無效比對內容，檢查情況如下：<br/><br/>"
    return header

def errorReason(url_status):
    if (url_status == "400"):
        return "．請求網址被伺服器判定格式錯誤"
    elif (url_status == "401"):
        return "．沒有授權"
    elif (url_status == "403"):
        return "．禁止存取"
    elif (url_status == "404"):
        str = "．找不到檔案或目錄<br/>"
        str += "．檔案網頁不存在或已移除<br/>"
        str += "．檔案網頁已被重新命名<br/>"
        str += "．檔案網頁已經刪除或移至其他位置<br/>"
        str += "．網址連結錯誤<br/>"
        return str
    elif (url_status == "500"):
        str = "．內部伺服器錯誤<br/>"
        str += "．無法存取要求的網頁，因為與該網頁相關的設定資料不正確<br/>"
        str += "．伺服器當機<br/>"
        str += "．網頁程式錯誤<br/>"
        str += "．資料庫連結錯誤<br/>"
        return str
    elif (url_status == "503"):
        return "．服務無法使用"
    elif (url_status == "-2"):
        return "．連結錯誤"
    elif (url_status == "-3"):
        return "．超過20秒而尚未回應網頁，提醒您：請檢查貴網站的呈現效能，並盡可能進行網站優化"
    elif (url_status == "-4"):
        return "．連結重新導向次數過多"
    elif (url_status == "-5"):
        str = "．偵測無法成功建立連結並回傳http狀態值<br/>"
        str += "．DNS查詢失敗，節點/伺服器名稱無法提供或未知 Nodename nor servname provided, or not known<br/>"
        str += "．網路無法使用 Network is unreachable<br/>"
        str += "．無法路由至主機，傳送端和接收端之間存在網路問題 No route to host<br/>"
        str += "．目標主機主動拒絕，連結不能建立 Connection refused<br/>"
        return str
    elif (url_status == "-6"):
        return "．憑證錯誤"
    elif (url_status == "-7"):
        return "．其他例外情形以致連結錯誤"
    elif (url_status == "-8"):
        return "．超過程式偵測所設定的回應時間門檻秒數而尚未回應網頁，提醒您：請檢查貴網站的呈現效能，並盡可能進行網站優化"
    elif (url_status == "-9"):
        return "．網頁無需SSO，但設定SSO"
    
    return ""
    
def error_code(url_status):
    if (url_status == "400"):
        return "http 錯誤 400 Bad Request "
    elif (url_status == "401"):
        return "http 錯誤 401 Unauthorized"
    elif (url_status == "403"):
        return "http 錯誤 403 Forbidden"
    elif (url_status == "404"):
        return "http 錯誤 404 Not Found"
    elif (url_status == "500"):
        return "http 錯誤 500 Internal Server Error"
    elif (url_status == "503"):
        return "http 錯誤 503 Service Unavailable"
    elif (url_status == "-2"):
        return "http 錯誤 -2 HTTPError"
    elif (url_status == "-3"):
        return "http 錯誤 -3 TIMEOUT"
    elif (url_status == "-4"):
        return "http 錯誤 -4 TooManyRedirects"
    elif (url_status == "-5"):
        return "http 錯誤 -5 ConnectionError"
    elif (url_status == "-6"):
        return "http 錯誤 -6 InvalidSchema"
    elif (url_status == "-7"):
        return "http 錯誤 -7 Exception"
    elif (url_status == "-8"):
        return "http 錯誤 -8 TIMEOUT WARNING"
    elif (url_status == "-9"):
        return "SSO 設定錯誤"
    
    return ""

"""
Main function
"""
if __name__ == "__main__":
    main()
