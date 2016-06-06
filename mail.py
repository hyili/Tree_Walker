#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import datetime

argv = sys.argv
if len(argv) < 4:
    print("exit")
    exit()
now = datetime.datetime.now()
offset = datetime.timedelta(hours=int(argv[2]))
result = now-offset
pattern = result.strftime("%Y-%m-%d %H")
print(pattern)

log = os.popen("grep \""+pattern+"\" .requests.log | wc -l | awk '{print $1}'")
for line in log:
    if int(line) > 2:
        print("Mail sent")
        os.popen("echo \"See details in attached files\" | mutt -a "+argv[1]+".* -s \"Tree Walker warning message.\" -- "+argv[3])
    else:
        print("Nothing")
