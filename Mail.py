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


def send_mail(sender, receiver, filenames, username, password):
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = "[Warning] Tree_Walker"
    msg.attach(MIMEText("See attached files for detail."))
    for filename in filenames:
        try:
            with open(filename, "rb") as attached_file:
                att = MIMEApplication(attached_file.read(), Name=filename)
                att['Content-Disposition'] = "attachment; filename=\""+filename+"\""
                msg.attach(att)
        except Exception as e:
            print(e)
            quit()

    try:
        smtp = smtplib.SMTP("smtpx.itri.org.tw")
        smtp.ehlo(name="itri.org.tw")
        smtp.login(user=username, password=password)
        smtp.sendmail(from_addr="FROM: "+sender, to_addrs=["TO: "+receiver], msg=msg.as_string())
    except Exception as e:
        print(e)
        quit()

if __name__ == "__main__":
    argv = sys.argv
    if len(argv) < 6:
        print("mail.py [tag] [time offset] [sender] [receiver] [files...]")
        exit()

    tag = argv[1]
    conf = Request.load_conf(".requests.conf", tag)
    offset = int(argv[2])
    index = datetime.datetime.now()-datetime.timedelta(hours=offset)
    sender = argv[3]
    receiver = argv[4]
    username = conf.payload["USER"]
    password = conf.payload["PASSWORD"]
    filenames = []
    for i in range(5, len(argv), 1):
        filenames.append(argv[i])

    count = 0
    log = os.popen("cat .requests.log")
    for line in log:
        part1 = line.split(" ")
        if part1[7] != "["+tag+"]":
            continue
        part2 = part1[1].split(",")
        log_time = datetime.datetime.strptime(part1[0]+" "+part2[0], "%Y-%m-%d %H:%M:%S")
        if index <= log_time:
            count += 1

    if count > 2:
        send_mail(sender, receiver, filenames, username, password)
        print("Mail sent")
    else:
        print("Nothing")
