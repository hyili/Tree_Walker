#!/bin/env python3

import subprocess
import csv
import sys
import pymssql
import datetime

# parse args
args = sys.argv
if len(args) == 2:
    filename = args[1]
else:
    exit(0)

# db info
dbhost = "###MASKED###"
dbport = "###MASKED###"
dbname = "###MASKED###"
dbuser = "###MASKED###"
dbpass = "###MASKED###"
# reason timeout redirection_timeout 待確定
dbmapping = ["check_time", "from_url", "", "checked_name", "checked_url", "", "", "rtn_status", "", "", "",
"spend_time", "reason", "search_level", "found_url_no", "searched_url_no", "timeout", "redirection_timeout"]
first_line = True

connection = pymssql.connect(dbhost, dbuser, dbpass, dbname, port=dbport)
cursor = connection.cursor()

# read csv
reader = None
try:
    with open(filename, "r") as f:
        reader = csv.reader(f)

        if reader is not None:
            for line in reader:
                if first_line:
                    first_line = False
                    continue
                time = datetime.datetime.strptime(line[0], "%Y/%m/%d-%H:%M:%S")
                strtime = datetime.datetime.strftime(time, "%Y-%m-%d %H:%M:%S")
                print("""INSERT INTO tbl_WebCheck_history ([ID], [check_time], [from_url], [checked_name], 
                        [checked_url], [current_url], [rtn_status], [spend_time], [reason], [search_level], [found_url_no],
                        [searched_url_no], [timeout], [redirection_timeout], [is_intra], [show_status], [found_level],
                        [context_found], [sso_check])
                        VALUES (%d, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""" %
                        (1, strtime, line[1], line[3], line[2], line[4], line[7], line[11], line[12], line[13], line[14], line[15], 
                        20, 20, "N", "400,401,403,404,500,503,-3,-5", "0", "N", "N"))
                cursor.execute("""INSERT INTO tbl_WebCheck_history ([ID], [check_time], [from_url], [checked_name], 
                        [checked_url], [current_url], [rtn_status], [spend_time], [reason],  [search_level], [found_url_no],
                        [searched_url_no], [timeout], [redirection_timeout], [is_intra], [show_status], [found_level],
                        [context_found], [sso_check])
                        VALUES (%d, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
                        (1, strtime, line[1], line[3], line[2], line[4], line[7], line[11], line[12], line[13], line[14], line[15], 
                        20, 20, "N", "400,401,403,404,500,503,-3,-5", "0", "N", "N"))
            connection.commit()
except Exception as e:
    print("%s", e)

exit(0)
