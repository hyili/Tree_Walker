#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import os
import csv
import datetime
from lxml import etree

import GlobalVars

import configparser
import pymssql  

"""
Output file generator using specified format
"""
def file_generator(history, logger, config):
    # TODO: global variable recheck

    # Prevent directory issue
    #output_filename = output_filename.replace("/", " ")

    if "JSON" in config.output_format:
        pass
    if "STDOUT" in config.output_format:
        print("Output.py")
        print("link_url:"+str(history[config.target_url]["link_url"]))
        print("link_name:"+str(history[config.target_url]["link_name"]))
        print("status_code:"+str(history[config.target_url]["status_code"]))
        print("context:"+str(history[config.target_url]["context"]))
        print("content_code:"+str(history[config.target_url]["content_code"]))
        #print("auth:"+str(history[config.target_url]["auth"]))
        print("start_time:"+str(history[config.target_url]["start_time"]))
        print("time_cost:"+str(history[config.target_url]["time_cost"]))
        print("reason:"+str(history[config.target_url]["reason"]))
        print("systep_id:"+str(history[config.target_url]["systep_id"]))
#write into db
    if "DB" in config.output_format:

        #"""
        DBconfig = configparser.ConfigParser()
        DBconfig.read('config/.config.conf')
        server = DBconfig.get('DB', 'SERVER').replace("\'","")
        username = DBconfig.get('DB', 'USERNAME').replace("\'","")
        password = DBconfig.get('DB', 'PASSWORD').replace("\'","")
        database = DBconfig.get('DB', 'DATABASE').replace("\'","")
        #"""
        #print(server+ " " + username + " " + password + " " + database)
        conn = pymssql.connect(server=server, user=username, password=password, database=database)
        #print(conn)
        cur = conn.cursor(as_dict=True)

        #link_url=str(history[config.target_url]["link_url"])
        status_code=str(history[config.target_url]["status_code"]) 
        systep_id=str(history[config.target_url]["systep_id"])
        start_time=str(history[config.target_url]["start_time"])
        restime = str(history[config.target_url]["time_cost"])
        content_code = str(history[config.target_url]["content_code"])
        #cur.execute("""UPDATE [SYSTEP] set [URL_STATUS] = %s WHERE [URL] = %s""",(status_code,link_url))

        cur.execute("SELECT URL_STATUS FROM SYSTEP_RECORDS WHERE [SYSTEP_ID]='1' ORDER BY START_TIME DESC")
        results = cur.fetchone()
        sso_status = results['URL_STATUS']
        

        
        cur.execute("""INSERT INTO [SYSTEP_RECORDS] ([SYSTEP_ID], [URL_STATUS], [START_TIME], [RESTIME], [CONTEXT_STATUS],[SSO_STATUS]) VALUES(%s, %s, %s, %s, %s, %s)""",(systep_id,status_code,str(start_time)[0:-3],restime,content_code,sso_status))



        #error
        if(status_code!="200" or content_code!= "0" or float(restime) >= float(config.timewarn)):
            print(systep_id)
            cur.execute("SELECT [CI_UID] FROM [SYSTEP] WHERE [ID]='"+str(systep_id)+"'")
            results = cur.fetchone()
            ciuid = results['CI_UID']
            cur.execute("""UPDATE [SYSINFO] set [SENDSIGN] = 1 WHERE [CI_UID] = %s""",(ciuid))
           
        conn.commit() #務必要commit進去        
        conn.close()
        print("DB Done")
        #print("link_url:"+str(history[config.target_url]["link_url"]))
        #print("link_name:"+str(history[config.target_url]["link_name"]))
        #print("status_code:"+str(history[config.target_url]["status_code"]))
        #print("context:"+str(history[config.target_url]["context"]))
        #print("content_code:"+str(history[config.target_url]["content_code"]))
        #print("auth:"+str(history[config.target_url]["auth"]))
        #print("time_cost:"+str(history[config.target_url]["time_cost"]))
        #print("reason:"+str(history[config.target_url]["reason"]))


