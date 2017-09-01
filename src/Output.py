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
    """
    if GlobalVars.total_output_links > 0:
        # TODO: logger reformat
        if "XML" in config.output_format:
            logger.warn("["+config.tag+"] filter_code: {"+str(config.filter_code)+"}, print_depth: {"+str(config.print_depth)+"} Generating "+output_filename+".xml ...")
        elif "CSV" in config.output_format:
            logger.warn("["+config.tag+"] filter_code: {"+str(config.filter_code)+"}, print_depth: {"+str(config.print_depth)+"} Generating "+output_filename+".csv ...")
    """
    """
    if "XML" in config.output_format:
        if config.sort == "URL":
            time = etree.Element("time")
            time.set("value", str(datetime.datetime.now()))
            total_link = etree.SubElement(time, "total_links")
            total_link.set("value", str(GlobalVars.total_links))
            total_output_link = etree.SubElement(time, "total_output_links")
            total_output_link.set("value", str(GlobalVars.total_output_links))
            for log in history:
                if history[log]["depth"] not in config.print_depth:
                    continue
                if history[log]["status_code"] not in config.filter_code or history[log]["contained_broken_link"] != 0:
                    locate = etree.SubElement(time, "locate")
                    locate.set("value", log)
                    try:
                        parent_url = etree.SubElement(locate, "parent_url")
                        parent_url.set("value", str(history[log]["parent_url"]))
                        link_url = etree.SubElement(locate, "link_url")
                        link_url.set("value", str(history[log]["link_url"]))
                        link_name = etree.SubElement(locate, "link_name")
                        link_name.set("value", str(history[log]["link_name"]))
                        current_url = etree.SubElement(locate, "current_url")
                        current_url.set("value", str(history[log]["current_url"]))
                        ssl_grade = etree.SubElement(locate, "ssl_grade")
                        ssl_grade.set("value", str(history[log]["ssl_grade"]))
                        ssl_report_url = etree.SubElement(locate, "ssl_report_url")
                        ssl_report_url.set("value", str(history[log]["ssl_report_url"]))
                        status_code = etree.SubElement(locate, "status_code")
                        status_code.set("value", str(history[log]["status_code"]))
                        contained_broken_link = etree.SubElement(locate, "contained_broken_link")
                        contained_broken_link.set("value", str(history[log]["contained_broken_link"]))
                        time_cost = etree.SubElement(locate, "time_cost")
                        time_cost.set("value", str(history[log]["time_cost"]))
                        reason = etree.SubElement(locate, "reason")
                        reason.set("value", str(history[log]["reason"]))
                    except Exception as e:
                        if config.debug_mode:
                            print("Output: "+str(e))
                        continue
            tree = etree.ElementTree(time)
            #with open(config.outputpath+"/"+output_filename+".xml", "ab", encoding="utf-8-sig") as xmlfile:
                #tree.write(xmlfile, pretty_print=True)
                #xmlfile.close()
        elif config.sort == "STATUS_CODE":
            sort_by_status = sorted(iter(history.values()), key=lambda x : x["status_code"])
            time = etree.Element("time")
            time.set("value", str(datetime.datetime.now()))
            total_link = etree.SubElement(time, "total_links")
            total_link.set("value", str(GlobalVars.total_links))
            total_output_link = etree.SubElement(time, "total_output_links")
            total_output_link.set("value", str(GlobalVars.total_output_links))
            for log in sort_by_status:
                if log["depth"] not in config.print_depth:
                    continue
                if log["status_code"] not in config.filter_code or log["contained_broken_link"] != 0:
                    locate = etree.SubElement(time, "locate")
                    locate.set("value", log["link_url"])
                    try:
                        parent_url = etree.SubElement(locate, "parent_url")
                        parent_url.set("value", str(log["parent_url"]))
                        link_url = etree.SubElement(locate, "link_url")
                        link_url.set("value", str(log["link_url"]))
                        link_name = etree.SubElement(locate, "link_name")
                        link_name.set("value", str(log["link_name"]))
                        current_url = etree.SubElement(locate, "current_url")
                        current_url.set("value", str(log["current_url"]))
                        ssl_grade = etree.SubElement(locate, "ssl_grade")
                        ssl_grade.set("value", str(log["ssl_grade"]))
                        ssl_report_url = etree.SubElement(locate, "ssl_report_url")
                        ssl_report_url.set("value", str(log["ssl_report_url"]))
                        status_code = etree.SubElement(locate, "status_code")
                        status_code.set("value", str(log["status_code"]))
                        contained_broken_link = etree.SubElement(locate, "contained_broken_link")
                        contained_broken_link.set("value", str(log["contained_broken_link"]))
                        time_cost = etree.SubElement(locate, "time_cost")
                        time_cost.set("value", str(log["time_cost"]))
                        reason = etree.SubElement(locate, "reason")
                        reason.set("value", str(log["reason"]))
                    except Exception as e:
                        if config.debug_mode:
                            print("Output: "+str(e))
                        continue
            tree = etree.ElementTree(time)
            #with open(config.outputpath+"/"+output_filename+".xml", "ab", encoding="utf-8-sig") as xmlfile:
                #tree.write(xmlfile, pretty_print=True)
                #xmlfile.close()
    """
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


