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
import argparse


"""
Argument init
"""
def arg_initialize(argv):
    parser = argparse.ArgumentParser(description="Start to send email.")
    parser.add_argument("--tag", default="DEFAULT", help="Specify tag in the conf.")
    parser.add_argument("--offset", default=2, type=int, help="Specify timing offset.")
    parser.add_argument("--sender", help="Specify sender email address.")
    parser.add_argument("--receiver", nargs="*", default=[], help="Specify receiver email addresses.")
    parser.add_argument("--ccreceiver", nargs="*", default=[], help="Specify ccreceiver email addresses.")
    parser.add_argument("--files", nargs="*", help="Specify files that want to attach.")
    return parser.parse_args()

"""
Send the Email
"""
def send_mail(sender, receivers, ccreceivers, filenames, username, password):
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = ", ".join(receivers)
    msg["Cc"] = ", ".join(ccreceivers)
    msg["Subject"] = "[Warning] Tree_Walker"
    msg.attach(MIMEText("See attached files for detail."))
    for filename in filenames:
        print(filename)
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
        smtp.sendmail(from_addr=sender, to_addrs=receivers+ccreceivers, msg=msg.as_string())
    except Exception as e:
        print(e)
        quit()

"""
Prepare to send
"""
def main():
    argv = sys.argv
    args = arg_initialize(argv)

    tag = args.tag
    offset = args.offset
    sender = args.sender
    receivers = args.receiver
    ccreceivers = args.ccreceiver
    index = datetime.datetime.now()-datetime.timedelta(hours=offset)

    conf = Request.load_config(".requests.conf", tag)
    username = conf.payload["USER"]
    password = conf.payload["PASSWORD"]

    filenames = args.files

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
        send_mail(sender, receivers, ccreceivers, filenames, username, password)
        print("Mail sent")
    else:
        print("Nothing")

"""
Main function
"""
if __name__ == "__main__":
    main()
