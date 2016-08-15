#!/usr/bin/env python3
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
    parser.add_argument("--tag", help="Specify tag in the conf.", required=True)
    parser.add_argument("--offset", type=int, help="Specify timing offset.")
    parser.add_argument("--sender", default="", help="Specify sender email address.")
    parser.add_argument("--receiver", nargs="*", help="Specify receiver email addresses.", required=True)
    parser.add_argument("--ccreceiver", nargs="*", default=[], help="Specify ccreceiver email addresses. Default is nothing.")
    parser.add_argument("--secretccreceiver", nargs="*", default=[], help="Specify secret ccreceiver email addresses. Default is nothing.")
    parser.add_argument("--subject", default="", help="Specify the email subject.")
    parser.add_argument("--content", default="", help="Specify the email content.")
    parser.add_argument("--files", nargs="*", default=[], help="Specify files that want to attach.")
    return parser.parse_args()

"""
Send the Email
"""
def send_mail(sender, receivers, ccreceivers, secretccreceivers, subject, content, filenames, username, password):
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = ", ".join(receivers)
    msg["Cc"] = ", ".join(ccreceivers)
    msg["Subject"] = subject
    _msg = MIMEText(content)
    _msg["Content-Type"] = "text/html"
    msg.attach(_msg)
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
        smtp.sendmail(from_addr=sender, to_addrs=receivers+ccreceivers+secretccreceivers, msg=msg.as_string())
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
    sender = args.sender
    receivers = args.receiver
    ccreceivers = args.ccreceiver
    secretccreceivers = args.secretccreceiver
    subject = args.subject
    content = args.content

    conf = Request.Config(filename=".requests.conf", tag=tag)
    conf.load_config()
    if sender == "":
        sender = conf.payload["USER"]+"@itri.org.tw"
    username = conf.payload["USER"]
    password = conf.payload["PASSWORD"]

    filenames = args.files

    if args.offset is not None:
        offset = args.offset
        index = datetime.datetime.now()-datetime.timedelta(hours=offset)

        count = 0
        log = os.popen("cat logs/main.log")
        for line in log:
            part1 = line.split(" ")
            if part1[7] != "["+tag+"]":
                continue
            part2 = part1[1].split(",")
            log_time = datetime.datetime.strptime(part1[0]+" "+part2[0], "%Y-%m-%d %H:%M:%S")
            if index <= log_time:
                count += 1

        if count > 2:
            send_mail(sender, receivers, ccreceivers, secretccreceivers, subject, content, filenames, username, password)
            print("Mail sent.")
        else:
            print("Do nothing, --help for details.")
    else:
        send_mail(sender, receivers, ccreceivers, secretccreceivers, subject, content, filenames, username, password)
        print("Mail sent.")

"""
Main function
"""
if __name__ == "__main__":
    main()
