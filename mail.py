#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import datetime
import smtplib
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import Request

if __name__ == "__main__":
    argv = sys.argv
    if len(argv) < 6:
        print("mail.py [tag] [time offset] [sender] [receiver] [files...]")
        exit()

    conf = Request.load_conf(".requests.conf", argv[1])
    result = datetime.datetime.now()-datetime.timedelta(hours=int(argv[2]))
    pattern = result.strftime("%Y-%m-%d %H")
    sender = argv[3]
    receiver = argv[4]
    username = conf.payload["USER"]
    password = conf.payload["PASSWORD"]
    filenames = []
    for i in range(5, len(argv), 1):
        filenames.append(argv[i])

    log = os.popen("grep \""+pattern+"\" .requests.log | wc -l | awk '{print $1}'")
    for line in log:
        if int(line) > 2:
            print("Mail sent")
            msg = MIMEMultipart()
            msg["From"] = sender
            msg["To"] = receiver
            msg["Subject"] = "[Warning] Tree_Walker"
            msg.attach(MIMEText("See attached files for detail."))
            for filename in filenames:
                with open(filename, "rb") as attached_file:
                    att = MIMEApplication(attached_file.read(), Name=filename)
                    att['Content-Disposition'] = "attachment; filename=\""+filename+"\""
                    msg.attach(att)

            smtp = smtplib.SMTP("smtpx.itri.org.tw")
            smtp.ehlo(name="itri.org.tw")
            smtp.login(user=username, password=password)
            smtp.sendmail(from_addr="FROM: "+sender, to_addrs=["TO: "+receiver], msg=msg.as_string())
        else:
            print("Nothing")
            msg = MIMEMultipart()
            msg["From"] = sender
            msg["To"] = receiver
            msg["Subject"] = "[Warning] Tree_Walker"
            msg.attach(MIMEText("See attached files for detail."))
            for filename in filenames:
                with open(filename, "rb") as attached_file:
                    att = MIMEApplication(attached_file.read(), Name=filename)
                    att['Content-Disposition'] = "attachment; filename=\""+filename+"\""
                    msg.attach(att)

            smtp = smtplib.SMTP("smtpx.itri.org.tw")
            smtp.ehlo(name="itri.org.tw")
            smtp.login(user=username, password=password)
            smtp.sendmail(from_addr="FROM: "+sender, to_addrs=["TO: "+receiver], msg=msg.as_string())
