#!/bin/env python3

import subprocess
import csv
import sys
import pymssql
import datetime

# parse args
args = sys.argv
if len(args) == 3:
	service_id = int(args[1])
	filename = args[2]
else:
        print("help: ./import_from_csv_to_DB.py [service_id] [csv_filename]")
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
				if service_id == 1:
					print("""INSERT INTO tbl_WebCheck_history ([service_id], [check_time], [from_url], [checked_name], 
							[checked_url], [current_url], [rtn_status], [spend_time], [reason], [search_level], [found_url_no],
							[searched_url_no], [timeout], [redirection_timeout], [is_intra], [show_status], [found_level],
							[context_found], [sso_check])
							VALUES (%d, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""" %
							(service_id, strtime, line[1], line[3], line[2], line[4], line[7], line[11], line[12],
							line[13], line[14], line[15], 20, 20, "Y", "200", "0", "N", "Y"))
					cursor.execute("""INSERT INTO tbl_WebCheck_history ([service_id], [check_time], [from_url], [checked_name], 
							[checked_url], [current_url], [rtn_status], [spend_time], [reason],  [search_level], [found_url_no],
							[searched_url_no], [timeout], [redirection_timeout], [is_intra], [show_status], [found_level],
							[context_found], [sso_check])
							VALUES (%d, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
							(service_id, strtime, line[1], line[3], line[2], line[4], line[7], line[11], line[12],
							line[13], line[14], line[15], 20, 20, "Y", "200", "0", "N", "Y"))
				elif service_id == 2:
					print("""INSERT INTO tbl_WebCheck_history ([service_id], [check_time], [from_url], [checked_name], 
							[checked_url], [current_url], [rtn_status], [spend_time], [reason], [search_level], [found_url_no],
							[searched_url_no], [timeout], [redirection_timeout], [is_intra], [show_status], [found_level],
							[context_found], [sso_check])
							VALUES (%d, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""" %
							(service_id, strtime, line[1], line[3], line[2], line[4], line[7], line[11], line[12],
							line[13], line[14], line[15], 20, 20, "N", "400,401,403,404,500,503,-3,-5", "0", "N", "N"))
					cursor.execute("""INSERT INTO tbl_WebCheck_history ([service_id], [check_time], [from_url], [checked_name], 
							[checked_url], [current_url], [rtn_status], [spend_time], [reason],  [search_level], [found_url_no],
							[searched_url_no], [timeout], [redirection_timeout], [is_intra], [show_status], [found_level],
							[context_found], [sso_check])
							VALUES (%d, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
							(service_id, strtime, line[1], line[3], line[2], line[4], line[7], line[11], line[12],
							line[13], line[14], line[15], 20, 20, "N", "400,401,403,404,500,503,-3,-5", "0", "N", "N"))
				elif service_id == 3:
					print("""INSERT INTO tbl_WebCheck_history ([service_id], [check_time], [from_url], [checked_name], 
							[checked_url], [current_url], [rtn_status], [spend_time], [reason], [search_level], [found_url_no],
							[searched_url_no], [timeout], [redirection_timeout], [is_intra], [show_status], [found_level],
							[context_found], [sso_check])
							VALUES (%d, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""" %
							(service_id, strtime, line[1], line[3], line[2], line[4], line[7], line[11], line[12],
							line[13], line[14], line[15], 20, 20, "N", "200", "0", "N", "N"))
					cursor.execute("""INSERT INTO tbl_WebCheck_history ([service_id], [check_time], [from_url], [checked_name], 
							[checked_url], [current_url], [rtn_status], [spend_time], [reason],  [search_level], [found_url_no],
							[searched_url_no], [timeout], [redirection_timeout], [is_intra], [show_status], [found_level],
							[context_found], [sso_check])
							VALUES (%d, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
							(service_id, strtime, line[1], line[3], line[2], line[4], line[7], line[11], line[12],
							line[13], line[14], line[15], 20, 20, "N", "200", "0", "N", "N"))
				elif service_id == 4:
					print("""INSERT INTO tbl_WebCheck_history ([service_id], [check_time], [from_url], [checked_name], 
							[checked_url], [rtn_status], [spend_time], [reason], [search_level], [found_url_no],
							[searched_url_no], [timeout], [redirection_timeout], [is_intra], [show_status],
							[context_found], [sso_check])
							VALUES (%d, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""" %
							(service_id, strtime, line[1], line[3], line[2], line[4], line[5], line[6], line[7], line[8],
							line[9], 20, 20, "N", "400,401,403,404,500,503,-3,-5", "N", "N"))
					cursor.execute("""INSERT INTO tbl_WebCheck_history ([service_id], [check_time], [from_url], [checked_name], 
							[checked_url], [rtn_status], [spend_time], [reason], [search_level], [found_url_no],
							[searched_url_no], [timeout], [redirection_timeout], [is_intra], [show_status],
							[context_found], [sso_check])
							VALUES (%d, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
							(service_id, strtime, line[1], line[3], line[2], line[4], line[5], line[6], line[7], line[8],
							line[9], 20, 20, "N", "400,401,403,404,500,503,-3,-5", "N", "N"))
			connection.commit()
except Exception as e:
	print("%s", e)

exit(0)
